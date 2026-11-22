import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AirQualityView } from "@/components/air-quality/air-quality-view";
import { LocationProvider } from "@/features/locations/location-context";
import { STORAGE_KEYS } from "@/features/store/storage";

const CURRENT = {
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
};

const FORECAST = {
  hourly: [
    { time: "2026-11-18T18:00:00Z", pm2_5: 80 },
    { time: "2026-11-18T19:00:00Z", pm2_5: 40 },
  ],
  provenance: {
    provider: "open-meteo",
    kind: "modelled",
    model: "CAMS ENSEMBLE",
    observed_at: "2026-11-18T17:00:00Z",
    fetched_at: "2026-11-18T17:02:11Z",
    age_minutes: 2,
    stale: false,
    source_type: "model_forecast",
    attribution: ["CAMS ENSEMBLE (Copernicus)"],
  },
};

const HISTORY = {
  daily: [
    { date: "2026-11-17", pm2_5: 90 },
    { date: "2026-11-18", pm2_5: 70 },
  ],
  provenance: {
    provider: "open-meteo",
    kind: "modelled",
    model: "CAMS ENSEMBLE",
    observed_at: "2026-11-18T17:00:00Z",
    fetched_at: "2026-11-18T17:02:11Z",
    age_minutes: 2,
    stale: false,
    source_type: "historical_observation",
    attribution: ["CAMS ENSEMBLE (Copernicus)"],
  },
};

const HEALTH = {
  providers: [
    {
      name: "open-meteo",
      status: "ok",
      configured: true,
      source_type: "model_forecast",
      supports_forecast: true,
      supports_history: true,
      supports_stations: false,
      circuit_state: "closed",
      attribution: ["Open-Meteo.com"],
      detail: "Model data responding.",
    },
  ],
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

function stubAirApi() {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const path = new URL(String(input), "http://localhost").pathname;
      const data = path.endsWith("/current")
        ? CURRENT
        : path.endsWith("/forecast")
          ? FORECAST
          : path.endsWith("/history")
            ? HISTORY
            : path.endsWith("/providers/health")
              ? HEALTH
              : null;
      if (!data) {
        return Promise.reject(new Error(`unexpected path ${path}`));
      }
      return Promise.resolve(
        new Response(JSON.stringify({ data, meta: {} }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      );
    }),
  );
}

function renderAir() {
  return render(
    <LocationProvider>
      <AirQualityView />
    </LocationProvider>,
  );
}

describe("AirQualityView", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("asks for a location rather than showing a fabricated reading", async () => {
    renderAir();

    expect(await screen.findByText("Choose a location to begin")).toBeInTheDocument();
  });

  it("renders current air, forecast summary, provider status and standards", async () => {
    seedLocation();
    stubAirApi();
    renderAir();

    expect(await screen.findByText("Trends & forecast")).toBeInTheDocument();
    expect(await screen.findByText("CPCB Air Quality Index")).toBeInTheDocument();
    expect((await screen.findAllByText("open-meteo")).length).toBeGreaterThan(0);
    expect(screen.getByText("Available")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "CPCB 2014 AQI categories" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "How the CPCB index is computed" }),
    ).toBeInTheDocument();
    expect(await screen.findByText("80 µg/m³", { exact: false })).toBeInTheDocument();
  });

  it("loads history only when the history tab is selected", async () => {
    seedLocation();
    stubAirApi();
    const user = userEvent.setup();
    renderAir();

    await user.click(await screen.findByRole("tab", { name: "7-day history" }));

    expect(await screen.findByText(/Reported history from the provider/)).toBeInTheDocument();
    expect(screen.getByText(/PM2.5 daily history/)).toBeInTheDocument();
  });

  it("labels a provider outage instead of showing cached values", async () => {
    seedLocation();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    renderAir();

    expect(await screen.findByText("Current air quality is not available")).toBeInTheDocument();
    expect(await screen.findByText(/Provider status could not be loaded/)).toBeInTheDocument();
  });
});
