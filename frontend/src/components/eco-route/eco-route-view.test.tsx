import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { EcoRouteView } from "@/components/eco-route/eco-route-view";
import { LocationProvider } from "@/features/locations/location-context";
import { STORAGE_KEYS } from "@/features/store/storage";

const COMPARISON = {
  route: { distance_km: 8.4, duration_min: 24, source: "haversine", is_estimate: true },
  modes: [
    {
      mode: "car",
      co2e_kg: 1.6,
      exposure_index: 78,
      duration_min: 24,
      recommended_for: ["air"],
    },
    {
      mode: "cycle",
      co2e_kg: null,
      exposure_index: null,
      duration_min: 32,
      recommended_for: ["carbon", "time"],
    },
  ],
  tradeoff_note: "Cycling has the lowest carbon cost.",
  assumptions: [{ key: "grid_factor", value: 0.71, source: "CEA 2023" }],
};

function seedLocation() {
  window.localStorage.setItem(
    STORAGE_KEYS.locations,
    JSON.stringify({
      items: [{ id: "loc-1", label: "Home", lat: 28.6139, lon: 77.209, source: "manual" }],
      activeId: "loc-1",
    }),
  );
}

function renderRoute() {
  return render(
    <LocationProvider>
      <EcoRouteView />
    </LocationProvider>,
  );
}

async function fillDestination(user: ReturnType<typeof userEvent.setup>) {
  await user.type(await screen.findByLabelText("Destination name"), "Office");
  await user.type(screen.getByLabelText("Latitude"), "28.5355");
  await user.type(screen.getByLabelText("Longitude"), "77.241");
}

describe("EcoRouteView", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("requires an active location before a comparison can start", async () => {
    renderRoute();

    expect(await screen.findByText(/No active location/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Compare selected modes/ })).toBeDisabled();
    expect(screen.getByText(/Enter a destination and compare/)).toBeInTheDocument();
  });

  it("renders the server comparison with provenance and never fills missing values", async () => {
    seedLocation();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve(
          new Response(JSON.stringify({ data: COMPARISON, meta: {} }), {
            status: 200,
            headers: { "content-type": "application/json" },
          }),
        ),
      ),
    );
    const user = userEvent.setup();
    renderRoute();

    await fillDestination(user);
    await user.click(screen.getByRole("button", { name: /Compare selected modes/ }));

    expect(await screen.findByText("8.4 km")).toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(within(table).getByRole("rowheader", { name: /Car/ })).toBeInTheDocument();
    expect(within(table).getByRole("rowheader", { name: /Cycling/ })).toBeInTheDocument();
    expect(within(table).getByText("1.6 kg")).toBeInTheDocument();
    expect(within(table).getByText("78 / 100")).toBeInTheDocument();
    expect(within(table).getByText("Not reported")).toBeInTheDocument();
    expect(screen.getByText("Cycling has the lowest carbon cost.")).toBeInTheDocument();
    expect(screen.getByText(/grid_factor/)).toBeInTheDocument();
  });

  it("shows field errors instead of sending an invalid destination", async () => {
    seedLocation();
    const user = userEvent.setup();
    renderRoute();

    await user.click(await screen.findByRole("button", { name: /Compare selected modes/ }));

    expect(await screen.findByText("Enter a name for this location.")).toBeInTheDocument();
    expect(screen.getByText("Enter a latitude.")).toBeInTheDocument();
    expect(screen.getByText("Enter a longitude.")).toBeInTheDocument();
  });

  it("saves selected travel preferences in this browser", async () => {
    seedLocation();
    const user = userEvent.setup();
    renderRoute();

    const cycling = await screen.findByRole("checkbox", { name: "Cycling" });
    await user.click(cycling);
    await user.click(screen.getByRole("button", { name: "Save preferences" }));

    expect(window.localStorage.getItem(STORAGE_KEYS.ecoPreferences)).toContain('"cycle"');
  });

  it("labels an unavailable comparison service without substituting an estimate", async () => {
    seedLocation();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    const user = userEvent.setup();
    renderRoute();

    await fillDestination(user);
    await user.click(screen.getByRole("button", { name: /Compare selected modes/ }));

    expect(await screen.findByText("Route comparison service not connected")).toBeInTheDocument();
    expect(screen.getByText(/The API could not be reached/)).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });
});
