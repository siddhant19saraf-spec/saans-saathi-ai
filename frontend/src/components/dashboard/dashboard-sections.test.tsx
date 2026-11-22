import { render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CurrentAirSection } from "@/components/dashboard/current-air-section";
import { InsightsPanel } from "@/components/dashboard/insights-panel";
import { ProvenancePanel } from "@/components/dashboard/provenance-panel";
import type { AirCurrent } from "@/features/air-quality/schemas";
import type { ResourceState } from "@/features/api/resource";
import type { SavedLocation } from "@/features/locations/schema";

const LOCATION: SavedLocation = {
  id: "loc-1",
  label: "Home",
  lat: 28.6139,
  lon: 77.209,
  source: "manual",
};

const READING = {
  pm2_5: 82,
  pm10: null,
  co_ug_m3: null,
  no2_ug_m3: 40,
  so2_ug_m3: null,
  o3_ug_m3: null,
};

function current(overrides: Partial<AirCurrent> = {}): AirCurrent {
  return {
    location: {
      requested: { lat: 28.61, lon: 77.21 },
      resolved: { lat: 28.6, lon: 77.2 },
      timezone: "Asia/Kolkata",
    },
    reading: READING,
    cpcb_aqi: {
      value: 201,
      category: "poor",
      dominant_pollutant: "pm2_5",
      method: "CPCB-2014",
      coverage: [],
      partial: true,
      basis: "PM2.5 sub-index",
    },
    provider_aqi: { us: 142, european: null, note: "Different breakpoints." },
    provenance: {
      provider: "open-meteo",
      kind: "modelled",
      source_type: "ground_observation",
      observed_at: "2026-11-18T17:00:00Z",
      fetched_at: "2026-11-18T17:02:11Z",
      age_minutes: 2,
      stale: false,
      attribution: ["CAMS ENSEMBLE"],
    },
    ...overrides,
  };
}

const NO_AQI: AirCurrent = {
  location: { requested: { lat: 28.61, lon: 77.21 } },
  reading: {
    pm2_5: null,
    pm10: null,
    co_ug_m3: null,
    no2_ug_m3: null,
    so2_ug_m3: null,
    o3_ug_m3: null,
  },
  cpcb_aqi: null,
  aqi_unavailable_reason: "The provider reported no PM2.5 or PM10.",
  provider_aqi: { us: null, european: null, note: "No index returned." },
  provenance: {
    provider: "openaq",
    kind: "station",
    source_type: "historical_observation",
    observed_at: null,
    fetched_at: "2026-11-18T17:02:11Z",
    age_minutes: 400,
    stale: true,
    attribution: ["OpenAQ"],
  },
};

function success(data: AirCurrent): ResourceState<AirCurrent> {
  return { status: "success", data };
}

describe("CurrentAirSection", () => {
  it("shows partial CPCB coverage, basis and only reported provider indexes", () => {
    render(
      <CurrentAirSection location={LOCATION} state={success(current())} retry={vi.fn()} />,
    );

    const currentRegion = screen.getByRole("region", { name: "Current conditions" });
    expect(within(currentRegion).getAllByText("Ground-station observation").length).toBeGreaterThan(0);
    expect(within(currentRegion).getByText(/Partial coverage/)).toBeInTheDocument();
    expect(within(currentRegion).getByText("Coverage: none reported")).toBeInTheDocument();
    expect(within(currentRegion).getByText("Basis: PM2.5 sub-index")).toBeInTheDocument();
    expect(within(currentRegion).getByText(/US AQI/)).toBeInTheDocument();
    expect(within(currentRegion).queryByText(/European AQI:/)).not.toBeInTheDocument();
    expect(within(currentRegion).getByText(/different scale/i)).toBeInTheDocument();
  });

  it("states why the AQI is missing and avoids an empty chart", () => {
    render(
      <CurrentAirSection location={LOCATION} state={success(NO_AQI)} retry={vi.fn()} />,
    );

    const currentRegion = screen.getByRole("region", { name: "Current conditions" });
    expect(within(currentRegion).getAllByText("Historical observation").length).toBeGreaterThan(0);
    expect(
      within(currentRegion).getByText("The provider reported no PM2.5 or PM10."),
    ).toBeInTheDocument();
    expect(
      within(currentRegion).getByText("No pollutant values were reported, so there is nothing to chart."),
    ).toBeInTheDocument();
    expect(
      within(currentRegion).getByText(
        "The provider did not return a US or European index for this hour.",
      ),
    ).toBeInTheDocument();
  });
});

describe("ProvenancePanel", () => {
  it("marks stale data and shows a station distance when provided", () => {
    render(
      <ProvenancePanel
        location={LOCATION}
        provenance={{
          provider: "openaq",
          kind: "satellite",
          observed_at: "2026-11-18T10:00:00Z",
          fetched_at: "2026-11-18T17:02:11Z",
          age_minutes: 422,
          freshness: "stale",
          stale: true,
          station: {
            id: "st-1",
            name: "ITO station",
            provider: "CPCB",
            latitude: 28.6,
            longitude: 77.2,
            distance_km: 2.35,
          },
          attribution: ["OpenAQ", "CPCB"],
        }}
      />,
    );

    expect(screen.getByText("Satellite")).toBeInTheDocument();
    expect(screen.getByText("Stale")).toBeInTheDocument();
    expect(screen.getByText(/ITO station/)).toBeInTheDocument();
    expect(screen.getByText(/2\.4 km away/)).toBeInTheDocument();
    expect(screen.getByText(/marked stale/)).toBeInTheDocument();
    expect(screen.queryByText("Model")).not.toBeInTheDocument();
  });

  it("labels a ground source and optional model without inventing a station", () => {
    render(
      <ProvenancePanel
        location={LOCATION}
        provenance={{
          provider: "cpcb",
          kind: "station",
          source_type: "ground_observation",
          model: "CAMS",
          observed_at: null,
          fetched_at: "2026-11-18T17:02:11Z",
          age_minutes: 10,
          freshness: "fresh",
          stale: false,
          attribution: ["CPCB"],
        }}
      />,
    );

    expect(screen.getByText("Ground-station observation")).toBeInTheDocument();
    expect(screen.getByText("Within window")).toBeInTheDocument();
    expect(screen.getByText("CAMS")).toBeInTheDocument();
    expect(screen.queryByText(/Monitoring station/)).not.toBeInTheDocument();
    expect(screen.queryByText(/atmospheric model/)).not.toBeInTheDocument();
  });
});

describe("InsightsPanel", () => {
  const SESSION_KEY = "saans.v1.session";

  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function seedSession() {
    window.localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        token: "token-abc",
        profileId: "profile-1",
        expiresAt: "2030-01-01T00:00:00Z",
        healthConsent: true,
      }),
    );
  }

  function envelope(data: unknown): Response {
    return new Response(JSON.stringify({ data, meta: {} }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }

  const PROFILE = {
    id: "hh-1",
    name: "Sharma household",
    size: 2,
    lat: 28.6,
    lon: 77.2,
    city: "New Delhi",
    timezone: "Asia/Kolkata",
    dwelling: "apartment_upper",
    cooking_fuel: "lpg",
    has_purifier: true,
    purifier_cadr: null,
    room_area_m2: null,
    ceiling_m: null,
    members: [
      { id: "m-1", age_band: "6-12", health_flags: ["asthma"], created_at: "2026-11-19T08:00:00Z" },
      { id: "m-2", age_band: "18-59", health_flags: [], created_at: "2026-11-19T08:00:00Z" },
    ],
    has_children: true,
    has_older_adults: false,
    has_health_flags: true,
    created_at: "2026-11-19T08:00:00Z",
    updated_at: "2026-11-19T08:00:00Z",
  };

  it("explains the first-run state without a session and without air data", () => {
    render(<InsightsPanel airState={{ status: "idle" }} />);

    expect(screen.getByText("No family session yet.")).toBeInTheDocument();
    expect(screen.getByText(/Activity precautions require current air-quality data/)).toBeInTheDocument();
    expect(screen.getByText(/No alert delivery channel is connected/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Create a household profile" })).toHaveAttribute(
      "href",
      "/family",
    );
  });

  it("uses the household and CPCB category only when data is present", async () => {
    seedSession();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(envelope(PROFILE)));

    render(<InsightsPanel airState={success(current())} />);

    expect(await screen.findByText("Sharma household")).toBeInTheDocument();
    expect(screen.getByText("2 members")).toBeInTheDocument();
    expect(screen.getByText("Asthma or reactive airways")).toBeInTheDocument();
    expect(screen.getByText(/Your profile includes health flags/)).toBeInTheDocument();
    expect(screen.getByText(/Poor conditions:/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Edit household profile" })).toHaveAttribute(
      "href",
      "/family",
    );
  });

  it("reports a family profile that cannot be loaded instead of guessing", async () => {
    seedSession();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));

    render(<InsightsPanel airState={{ status: "unavailable", message: "offline", code: "X" }} />);

    await waitFor(() =>
      expect(
        screen.getByText("The family profile could not be loaded from this session."),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText(/Add age bands and optional general health flags/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Create a household profile" })).toBeInTheDocument();
  });
});
