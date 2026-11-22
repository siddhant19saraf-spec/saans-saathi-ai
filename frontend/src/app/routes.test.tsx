import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type * as React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import MarketingLayout from "@/app/(marketing)/layout";
import LandingPage from "@/app/(marketing)/page";
import AirQualityPage from "@/app/(app)/air-quality/page";
import CopilotPage from "@/app/(app)/copilot/page";
import DashboardPage from "@/app/(app)/dashboard/page";
import EcoRoutePage from "@/app/(app)/eco-route/page";
import FamilyPage from "@/app/(app)/family/page";
import ImpactPage from "@/app/(app)/impact/page";
import IndoorShieldPage from "@/app/(app)/indoor-shield/page";
import MapPage from "@/app/(app)/map/page";
import SettingsPage from "@/app/(app)/settings/page";
import SmartRoutinePage from "@/app/(app)/smart-routine/page";
import RouteError from "@/app/error";
import Loading from "@/app/loading";
import NotFound from "@/app/not-found";
import { LocationProvider } from "@/features/locations/location-context";

const PAGES: Array<{ name: string; Page: () => React.ReactElement; heading: RegExp }> = [
  { name: "dashboard", Page: DashboardPage, heading: /air intelligence/i },
  { name: "air quality", Page: AirQualityPage, heading: /air quality in detail/i },
  { name: "map", Page: MapPage, heading: /choose a place on the map/i },
  { name: "family", Page: FamilyPage, heading: /family intelligence/i },
  { name: "smart routine", Page: SmartRoutinePage, heading: /smartroutine/i },
  { name: "indoor shield", Page: IndoorShieldPage, heading: /indoorshield/i },
  { name: "eco route", Page: EcoRoutePage, heading: /ecoroute/i },
  { name: "impact", Page: ImpactPage, heading: /impact/i },
  { name: "copilot", Page: CopilotPage, heading: /saans ai copilot/i },
  { name: "settings", Page: SettingsPage, heading: /settings/i },
];

function renderPage(Page: () => React.ReactElement) {
  return render(
    <LocationProvider>
      <Page />
    </LocationProvider>,
  );
}

beforeEach(() => {
  window.localStorage.clear();
  // Pages must render their own unavailable states rather than reaching the
  // network in a unit test.
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("marketing landing route", () => {
  it("renders the full landing page inside its header and footer", () => {
    render(
      <MarketingLayout>
        <LandingPage />
      </MarketingLayout>,
    );

    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Site" })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Open dashboard" })[0]).toHaveAttribute(
      "href",
      "/dashboard",
    );
    expect(screen.getAllByText(/Every Breath Matters/).length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Build the habit/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Dashboard" })).toHaveAttribute("href", "/dashboard");
    expect(screen.getByText(/map tiles © OpenStreetMap contributors/i)).toBeInTheDocument();
  });

  it("opens the mobile site navigation", async () => {
    const user = userEvent.setup();
    render(
      <MarketingLayout>
        <LandingPage />
      </MarketingLayout>,
    );

    await user.click(screen.getByRole("button", { name: "Open navigation menu" }));

    const dialog = await screen.findByRole("dialog", { name: "Site navigation" });
    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getAllByRole("link", { name: "FAQ" }).length).toBeGreaterThan(0);
    expect(within(dialog).getByRole("link", { name: "Open dashboard" })).toHaveAttribute(
      "href",
      "/dashboard",
    );
  });
});

describe("app routes", () => {
  it.each(PAGES)("renders the $name page header", async ({ Page, heading }) => {
    renderPage(Page);

    expect(
      await screen.findByRole("heading", { level: 1, name: heading }),
    ).toBeInTheDocument();
  });
});

describe("route chrome", () => {
  it("renders a recoverable error with a reference code", async () => {
    const error = Object.assign(new Error("boom"), { digest: "ref-123" });
    const reset = vi.fn();
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    const user = userEvent.setup();

    render(<RouteError error={error} reset={reset} />);

    expect(screen.getByRole("heading", { name: "Something went wrong" })).toBeInTheDocument();
    expect(screen.getByText("Reference: ref-123")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(reset).toHaveBeenCalledTimes(1);
    expect(consoleError).toHaveBeenCalledWith("Unhandled route error", "ref-123");
  });

  it("renders a 404 page with a way home", () => {
    render(<NotFound />);

    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to home" })).toHaveAttribute("href", "/");
  });

  it("announces the loading state", () => {
    render(<Loading />);

    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
    expect(screen.getByText("Loading content")).toBeInTheDocument();
  });
});
