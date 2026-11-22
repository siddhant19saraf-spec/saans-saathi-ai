import { render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardView } from "@/components/dashboard/dashboard-view";
import { LocationProvider } from "@/features/locations/location-context";
import { STORAGE_KEYS } from "@/features/store/storage";

function seedLocation() {
  window.localStorage.setItem(
    STORAGE_KEYS.locations,
    JSON.stringify({
      items: [{ id: "loc-1", label: "Home", lat: 28.6139, lon: 77.209, source: "manual" }],
      activeId: "loc-1",
    }),
  );
}

function renderDashboard() {
  return render(
    <LocationProvider>
      <DashboardView />
    </LocationProvider>,
  );
}

describe("DashboardView", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("asks for a location instead of inventing a reading", async () => {
    renderDashboard();

    expect(await screen.findByText("Choose a location to begin")).toBeInTheDocument();
    expect(screen.getByText(/No readings are generated locally/)).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("shows a labelled unavailable state when the air service fails", async () => {
    seedLocation();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));

    renderDashboard();

    const current = await screen.findByRole("region", { name: "Current conditions" });
    expect(within(current).getByText("Current air quality is not available")).toBeInTheDocument();
    expect(within(current).getByText(/Check that the backend is running/)).toBeInTheDocument();
    expect(within(current).queryByRole("img")).not.toBeInTheDocument();
  });

  it("renders the selected location's provenance only after a real response", async () => {
    seedLocation();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve(
          new Response(
            JSON.stringify({
              data: {
                location: {
                  requested: { lat: 28.61, lon: 77.21 },
                  resolved: { lat: 28.6, lon: 77.2 },
                  timezone: "Asia/Kolkata",
                },
                reading: {
                  pm2_5: 75.2,
                  pm10: 76.4,
                  co_ug_m3: 1581,
                  no2_ug_m3: 63.7,
                  so2_ug_m3: 27.9,
                  o3_ug_m3: 26,
                },
                cpcb_aqi: {
                  value: 151,
                  category: "moderate",
                  dominant_pollutant: "pm2_5",
                  method: "CPCB-2014",
                  coverage: ["pm2_5", "pm10", "no2", "so2", "o3", "co"],
                  partial: false,
                },
                provider_aqi: { us: 166, european: 73, note: "Different scales" },
                provenance: {
                  provider: "open-meteo",
                  kind: "modelled",
                  model: "CAMS ENSEMBLE",
                  observed_at: "2026-11-18T17:00:00Z",
                  fetched_at: "2026-11-18T17:02:11Z",
                  age_minutes: 2,
                  stale: false,
                  attribution: ["CAMS ENSEMBLE (Copernicus)", "Open-Meteo.com"],
                },
              },
              meta: {},
            }),
            { status: 200, headers: { "content-type": "application/json" } },
          ),
        ),
      ),
    );

    renderDashboard();

    const current = await screen.findByRole("region", { name: "Current conditions" });
    expect(within(current).getByText("CPCB Air Quality Index")).toBeInTheDocument();
    expect(within(current).getAllByText("Moderate").length).toBeGreaterThan(0);
    expect(
      within(current).getByRole("img", { name: "CPCB AQI 151, Moderate category" }),
    ).toBeInTheDocument();
    expect(within(current).getByText("CAMS ENSEMBLE (Copernicus)")).toBeInTheDocument();
  });
});
