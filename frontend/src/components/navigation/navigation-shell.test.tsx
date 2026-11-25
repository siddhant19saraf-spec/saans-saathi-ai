import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AppShell } from "@/components/layout/app-shell";
import { Logo } from "@/components/layout/logo";
import { SkipLink } from "@/components/layout/skip-link";
import { Breadcrumbs } from "@/components/navigation/breadcrumbs";
import { CommandSearch } from "@/components/navigation/command-search";
import { LocationSwitcher } from "@/components/navigation/location-switcher";
import { allNavItems } from "@/components/navigation/nav-config";
import { Notifications } from "@/components/navigation/notifications";
import { UserMenu } from "@/components/navigation/user-menu";
import { LocationProvider } from "@/features/locations/location-context";
import { STORAGE_KEYS } from "@/features/store/storage";

const navigation = vi.hoisted(() => ({
  push: vi.fn(),
  pathname: { current: "/dashboard" },
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: navigation.push }),
  usePathname: () => navigation.pathname.current,
}));

function seedLocations() {
  window.localStorage.setItem(
    STORAGE_KEYS.locations,
    JSON.stringify({
      items: [
        { id: "loc-1", label: "Home", lat: 28.6139, lon: 77.209, source: "manual" },
        { id: "loc-2", label: "Work", lat: 19.076, lon: 72.8777, source: "device" },
      ],
      activeId: "loc-1",
    }),
  );
}

function renderWithLocations(children: React.ReactNode) {
  return render(<LocationProvider>{children}</LocationProvider>);
}

beforeEach(() => {
  window.localStorage.clear();
  navigation.push.mockReset();
  navigation.pathname.current = "/dashboard";
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("CommandSearch", () => {
  it("opens from the keyboard, filters pages and opens the active result", async () => {
    const user = userEvent.setup();
    render(<CommandSearch />);

    act(() => {
      fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    });

    const input = await screen.findByRole("combobox", { name: "Search pages and tools" });
    expect(screen.getAllByRole("option")).toHaveLength(allNavItems.length);

    await user.type(input, "copilot");
    expect(screen.getAllByRole("option")).toHaveLength(1);

    await user.keyboard("{Enter}");
    expect(navigation.push).toHaveBeenCalledWith("/copilot");
  });

  it("moves the active option with arrow keys and reports empty results", async () => {
    const user = userEvent.setup();
    render(<CommandSearch />);

    await user.click(screen.getByRole("button", { name: "Search pages" }));
    const input = await screen.findByRole("combobox", { name: "Search pages and tools" });

    const firstActive = input.getAttribute("aria-activedescendant");
    await user.keyboard("{ArrowDown}");
    expect(input.getAttribute("aria-activedescendant")).not.toBe(firstActive);
    await user.keyboard("{ArrowUp}");
    expect(input.getAttribute("aria-activedescendant")).toBe(firstActive);

    await user.type(input, "zzzz-no-page");
    expect(screen.getByText(/No pages match/)).toBeInTheDocument();
    expect(screen.queryByRole("option")).not.toBeInTheDocument();
  });

  it("closes with Escape and clears the query", async () => {
    const user = userEvent.setup();
    render(<CommandSearch />);

    await user.click(screen.getByRole("button", { name: "Search pages" }));
    await user.type(await screen.findByRole("combobox"), "map");
    await user.keyboard("{Escape}");

    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Search pages" }));
    expect(await screen.findByRole("combobox")).toHaveValue("");
  });
});

describe("LocationSwitcher", () => {
  it("lists saved places, changes the active place and removes one", async () => {
    seedLocations();
    const user = userEvent.setup();
    renderWithLocations(<LocationSwitcher />);

    await user.click(
      screen.getByRole("button", { name: "Change location. Current location: Home" }),
    );
    const workOptions = await screen.findAllByRole("button", { name: /^Work/ });
    await user.click(workOptions[0]!);

    await waitFor(() =>
      expect(window.localStorage.getItem(STORAGE_KEYS.locations)).toContain('"activeId":"loc-2"'),
    );

    await user.click(
      screen.getByRole("button", { name: "Change location. Current location: Work" }),
    );
    await user.click(await screen.findByRole("button", { name: "Remove Work" }));

    await waitFor(() =>
      expect(JSON.parse(window.localStorage.getItem(STORAGE_KEYS.locations) ?? "{}").items).toHaveLength(1),
    );
  });

  it("adds the device location when permission is granted", async () => {
    Object.defineProperty(navigator, "geolocation", {
      configurable: true,
      value: {
        getCurrentPosition: (success: PositionCallback) =>
          success({ coords: { latitude: 19.076, longitude: 72.8777 } } as GeolocationPosition),
      },
    });
    const user = userEvent.setup();
    renderWithLocations(<LocationSwitcher />);

    await user.click(screen.getByRole("button", { name: "Set a location" }));
    await user.click(await screen.findByRole("button", { name: "Use my location" }));

    await waitFor(() =>
      expect(window.localStorage.getItem(STORAGE_KEYS.locations)).toContain('"label":"My location"'),
    );
  });

  it("explains a denied device location instead of guessing a place", async () => {
    Object.defineProperty(navigator, "geolocation", {
      configurable: true,
      value: {
        getCurrentPosition: (_success: PositionCallback, error?: PositionErrorCallback) =>
          error?.({
            code: 1,
            PERMISSION_DENIED: 1,
            TIMEOUT: 3,
            POSITION_UNAVAILABLE: 2,
            message: "denied",
          } as GeolocationPositionError),
      },
    });
    const user = userEvent.setup();
    renderWithLocations(<LocationSwitcher />);

    await user.click(screen.getByRole("button", { name: "Set a location" }));
    await user.click(await screen.findByRole("button", { name: "Use my location" }));

    expect(
      await screen.findByText(
        "Location permission was denied. Enter coordinates instead.",
      ),
    ).toBeInTheDocument();
    expect(window.localStorage.getItem(STORAGE_KEYS.locations)).toBeNull();
  });

  it("shows the empty state and opens the coordinate form", async () => {
    const user = userEvent.setup();
    renderWithLocations(<LocationSwitcher />);

    await user.click(screen.getByRole("button", { name: "Set a location" }));
    expect(screen.getByText(/No locations saved yet/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Add coordinates" }));
    expect(await screen.findByRole("dialog", { name: "Add a location" })).toBeInTheDocument();
  });
});

describe("Notifications and profile menu", () => {
  it("states that notifications are not connected and shows local preferences", async () => {
    window.localStorage.setItem(
      STORAGE_KEYS.notificationPreferences,
      JSON.stringify({ airQualityAlerts: true, routineReminders: false, weeklyImpact: true }),
    );
    const user = userEvent.setup();
    render(<Notifications />);

    await user.click(screen.getByRole("button", { name: "Notifications" }));

    expect(await screen.findByText("No notifications yet")).toBeInTheDocument();
    expect(screen.getByText("Not connected")).toBeInTheDocument();
    expect(screen.getAllByText("On (local)")).toHaveLength(2);
    expect(screen.getAllByText("Off").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("link", { name: "Manage notification preferences" }),
    ).toHaveAttribute("href", "/settings#notifications");
  });

  it("keeps a guest profile menu with real destinations", async () => {
    const user = userEvent.setup();
    render(<UserMenu />);

    await user.click(screen.getByRole("button", { name: "Open profile menu" }));

    expect(await screen.findByText(/No account is connected/)).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Settings" })).toHaveAttribute(
      "href",
      "/settings",
    );
    expect(screen.getByRole("menuitem", { name: "Data sources & privacy" })).toHaveAttribute(
      "href",
      "/settings#data-sources",
    );
    expect(screen.getByRole("menuitem", { name: "About this build" })).toHaveAttribute(
      "href",
      "/#about",
    );
  });
});

describe("Breadcrumbs", () => {
  it("shows the group and current page for a known route", () => {
    navigation.pathname.current = "/smart-routine";
    render(<Breadcrumbs />);

    const nav = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(within(nav).getByRole("link", { name: "Home" })).toHaveAttribute("href", "/");
    expect(within(nav).getByText("Personal protection")).toBeInTheDocument();
    expect(within(nav).getByText("SmartRoutine")).toHaveAttribute("aria-current", "page");
  });

  it("renders nothing outside the navigation tree", () => {
    navigation.pathname.current = "/unknown";
    const { container } = render(<Breadcrumbs />);

    expect(container).toBeEmptyDOMElement();
  });
});

describe("Layout chrome", () => {
  it("renders a single main landmark, navigation and honest footer", () => {
    render(
      <AppShell>
        <h1>Today</h1>
      </AppShell>,
    );

    expect(screen.getByRole("main")).toHaveAttribute("id", "main-content");
    expect(screen.getByRole("heading", { name: "Today" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Primary" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search pages" })).toBeInTheDocument();
    expect(screen.getByText(/Every data surface states its source/)).toBeInTheDocument();
    expect(screen.getByText(/data surfaces disclose their source/)).toBeInTheDocument();
  });

  it("renders the skip link first and a compact logo link", () => {
    render(
      <>
        <SkipLink />
        <Logo compact />
      </>,
    );

    expect(screen.getByRole("link", { name: "Skip to main content" })).toHaveAttribute(
      "href",
      "#main-content",
    );
    const logo = screen.getByRole("link", { name: /SAANS SAATHI AI/ });
    expect(logo).toHaveAttribute("href", "/");
    expect(screen.queryByText("Air intelligence")).not.toBeInTheDocument();
  });

  it("allows the logo target to be overridden", () => {
    render(<Logo href="/dashboard" />);
    expect(screen.getByRole("link", { name: /SAANS SAATHI AI/ })).toHaveAttribute(
      "href",
      "/dashboard",
    );
  });
});
