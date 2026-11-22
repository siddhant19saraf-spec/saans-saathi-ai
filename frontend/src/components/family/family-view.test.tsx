import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { FamilyView } from "./family-view";

const FUTURE = "2030-01-01T00:00:00+00:00";
const NOW = "2026-11-19T08:00:00+00:00";
const SESSION_KEY = "saans.v1.session";

const PROFILE = {
  id: "hh-1",
  name: "Sharma household",
  size: 2,
  lat: 28.6139,
  lon: 77.209,
  city: "New Delhi",
  timezone: "Asia/Kolkata",
  dwelling: "apartment_upper",
  cooking_fuel: "lpg",
  has_purifier: true,
  purifier_cadr: 300,
  room_area_m2: 24,
  ceiling_m: 2.7,
  members: [
    { id: "m-1", age_band: "6-12", health_flags: ["asthma"], created_at: NOW },
    { id: "m-2", age_band: "18-59", health_flags: [], created_at: NOW },
  ],
  has_children: true,
  has_older_adults: false,
  has_health_flags: true,
  created_at: NOW,
  updated_at: NOW,
};

const PREFERENCES = {
  household_id: "hh-1",
  locale: "en-IN",
  activity_windows: [
    {
      id: "school-run",
      title: "School run",
      activity: "school_commute",
      start: "07:30",
      duration_min: 45,
      intensity: "moderate",
      venue: "outdoor",
      days: ["mon", "tue", "wed", "thu", "fri"],
      flexibility_min: 60,
      indoor_alternative: "Use public transport",
      transport_mode: "walk",
    },
  ],
  alert_threshold_aqi: 120,
  transport_mode: "walk",
  notifications_enabled: true,
  notify_alerts: true,
  notify_daily_summary: false,
  quiet_hours_start: null,
  quiet_hours_end: null,
  created_at: NOW,
  updated_at: NOW,
};

const POLLUTION_CONTEXT = {
  provider: "open-meteo",
  source_type: "model_forecast",
  aqi: 235,
  category: "poor",
  pm2_5: 110,
  pm10: 176,
  observed_at: NOW,
  fetched_at: NOW,
  age_minutes: 12,
  stale: false,
  forecast_used: false,
  forecast_only: false,
  guidance_basis: "cpcb_aqi",
  guidance_basis_label: "CPCB AQI (2014 method)",
  aqi_unavailable_reason: null,
  attribution: ["Open-Meteo"],
};

const RECOMMENDATION = {
  recommendation_id: "rec-1",
  activity: "school_commute",
  activity_title: "School run",
  recommended_action: "move_indoor",
  action_label: "Move this activity indoors",
  reason:
    "CPCB AQI is 235 (poor) from open-meteo. This commute is planned as a walk, so the rules engine moves it indoors. General guidance, not medical advice.",
  relevant_pollution_context: POLLUTION_CONTEXT,
  alternative_activity: "Use public transport or a vehicle with recirculated air",
  suggested_time: null,
  suggested_at: null,
  data_source: "CPCB 2014 AQI from open-meteo (model forecast)",
  attribution: ["Open-Meteo"],
  generated_at: NOW,
  uncertainty_information: ["Modelled values can differ from street-level monitors."],
  evidence: [
    {
      source: "CPCB National Air Quality Index (2014), Central Pollution Control Board",
      note: "AQI categories and PM2.5 sub-index breakpoints.",
    },
  ],
  rule_id: "FAM-009",
  rule_version: "family-rules-1.0.0",
  severity: "poor",
  confidence: "high",
};

const OLDER_RECOMMENDATION = {
  ...RECOMMENDATION,
  recommendation_id: "rec-0",
  activity: "outdoor_play",
  activity_title: "Park time",
  recommended_action: "check_back",
  action_label: "Check again before going outside",
  reason: "No validated pollution reading is available for this location.",
  relevant_pollution_context: {
    ...POLLUTION_CONTEXT,
    provider: null,
    source_type: null,
    aqi: null,
    category: null,
    pm2_5: null,
    pm10: null,
    observed_at: null,
    fetched_at: null,
    age_minutes: null,
    guidance_basis: "none",
    guidance_basis_label: "No validated pollution data",
    aqi_unavailable_reason: "No current or forecast air-quality data is available.",
    attribution: [],
  },
  alternative_activity: null,
  suggested_time: null,
  suggested_at: null,
  data_source: "No validated current or forecast reading",
  attribution: [],
  uncertainty_information: ["No pollution data was available when this was generated."],
  evidence: [],
  rule_id: "FAM-001",
  confidence: "low",
};

const BATCH = {
  household_id: "hh-1",
  generated_at: NOW,
  rules_version: "family-rules-1.0.0",
  pollution_context: POLLUTION_CONTEXT,
  recommendations: [RECOMMENDATION],
  ai_explanation: {
    status: "available",
    text: "Air quality is poor, so the school run is moved indoors.",
    model: "gemini-test",
    reason: null,
  },
  disclaimer: "General air-quality guidance only. This is not medical advice.",
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function envelope(data: unknown): Response {
  return json({ data, meta: { request_id: "test-request" } });
}

function problem(status: number, code: string, detail: string): Response {
  return json(
    { type: "about:blank", title: "Error", status, detail, code, request_id: "test-request" },
    status,
  );
}

function seedSession(healthConsent = true): void {
  localStorage.setItem(
    SESSION_KEY,
    JSON.stringify({
      token: "token-abc",
      profileId: "profile-1",
      expiresAt: FUTURE,
      healthConsent,
    }),
  );
}

type Route = (url: URL, init: RequestInit) => Response | Promise<Response>;

function mockFetch(route: Route) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(input.toString());
    return route(url, init ?? {});
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("FamilyView session bootstrap", () => {
  it("starts an anonymous session explicitly and then shows the empty profile form", async () => {
    const fetchMock = mockFetch((url, init) => {
      if (url.pathname === "/api/v1/sessions" && init.method === "POST") {
        return envelope({ token: "new-token", expires_at: FUTURE, profile_id: "profile-new" });
      }
      if (url.pathname === "/api/v1/family/profile") {
        return problem(404, "NOT_FOUND", "No household exists for this profile.");
      }
      return problem(500, "UNEXPECTED", `Unexpected route ${url.pathname}`);
    });
    const user = userEvent.setup();

    render(<FamilyView />);

    expect(screen.getByRole("heading", { name: "Start an anonymous session" })).toBeVisible();
    expect(fetchMock).not.toHaveBeenCalled();

    await user.click(screen.getByRole("checkbox", { name: /Also store general health flags/i }));
    await user.click(screen.getByRole("button", { name: "Start session" }));

    await screen.findByRole("heading", { name: "Create the household profile" });

    const sessionCall = fetchMock.mock.calls.find(
      ([input, init]) =>
        new URL(input.toString()).pathname === "/api/v1/sessions" && init?.method === "POST",
    );
    expect(sessionCall).toBeDefined();
    expect(JSON.parse(String(sessionCall?.[1]?.body))).toEqual({
      consent_version: "2026-11",
      health_consent: true,
    });

    const stored = JSON.parse(localStorage.getItem(SESSION_KEY) ?? "{}");
    expect(stored).toMatchObject({ token: "new-token", healthConsent: true });

    const profileCall = fetchMock.mock.calls.find(
      ([input]) => new URL(input.toString()).pathname === "/api/v1/family/profile",
    );
    expect((profileCall?.[1]?.headers as Record<string, string>).Authorization).toBe(
      "Bearer new-token",
    );
  });
});

describe("FamilyView with a stored session", () => {
  it("renders the saved profile, generates recommendations and keeps history", async () => {
    seedSession();
    let generated = false;
    const fetchMock = mockFetch((url, init) => {
      if (url.pathname === "/api/v1/family/profile") {
        return envelope(PROFILE);
      }
      if (url.pathname === "/api/v1/family/preferences") {
        return envelope(PREFERENCES);
      }
      if (url.pathname === "/api/v1/family/recommendations/generate" && init.method === "POST") {
        generated = true;
        return envelope(BATCH);
      }
      if (url.pathname === "/api/v1/family/recommendations") {
        return envelope({
          items: generated ? [RECOMMENDATION, OLDER_RECOMMENDATION] : [OLDER_RECOMMENDATION],
          limit: 20,
          offset: 0,
        });
      }
      return problem(500, "UNEXPECTED", `Unexpected route ${url.pathname}`);
    });
    const user = userEvent.setup();

    render(<FamilyView />);

    expect(await screen.findByText("Sharma household")).toBeVisible();
    expect(screen.getByText("Member 1 · 6–12 years")).toBeVisible();
    expect(screen.getByText("Health consent granted")).toBeVisible();

    expect(await screen.findByText("Activity preferences")).toBeVisible();
    expect(screen.getByDisplayValue("School run")).toBeInTheDocument();
    expect(
      await screen.findByText("No validated pollution reading is available for this location."),
    ).toBeVisible();
    expect(screen.getByText("Check again before going outside")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Generate recommendations" }));

    expect(await screen.findByText("Latest recommendations")).toBeVisible();
    expect(screen.getByText("Move this activity indoors")).toBeVisible();
    expect(
      screen.getByText("Use public transport or a vehicle with recirculated air"),
    ).toBeVisible();
    expect(screen.getByText("Modelled forecast")).toBeVisible();
    expect(
      screen.getByText(/Air quality is poor, so the school run is moved indoors/),
    ).toBeVisible();
    expect(screen.queryByText("Check again before going outside")).toBeVisible();
    expect(screen.getByText("Park time")).toBeVisible();

    const generationCall = fetchMock.mock.calls.find(
      ([input, init]) =>
        new URL(input.toString()).pathname === "/api/v1/family/recommendations/generate" &&
        init?.method === "POST",
    );
    expect(generationCall).toBeDefined();
  });

  it("shows a deterministic recommendation with an unavailable AI explanation", async () => {
    seedSession();
    const unavailableBatch = {
      ...BATCH,
      ai_explanation: { status: "unavailable", text: null, model: null, reason: "timeout" },
    };
    mockFetch((url, init) => {
      if (url.pathname === "/api/v1/family/profile") {
        return envelope(PROFILE);
      }
      if (url.pathname === "/api/v1/family/preferences") {
        return envelope(PREFERENCES);
      }
      if (url.pathname === "/api/v1/family/recommendations/generate" && init.method === "POST") {
        return envelope(unavailableBatch);
      }
      if (url.pathname === "/api/v1/family/recommendations") {
        return envelope({ items: [], limit: 20, offset: 0 });
      }
      return problem(500, "UNEXPECTED", `Unexpected route ${url.pathname}`);
    });
    const user = userEvent.setup();

    render(<FamilyView />);
    await screen.findByText("Sharma household");

    await user.click(screen.getByRole("button", { name: "Generate recommendations" }));

    expect(await screen.findByText(/AI explanation unavailable \(timeout\)/)).toBeVisible();
    expect(screen.getByText("Move this activity indoors")).toBeVisible();
  });
});

describe("FamilyView profile creation", () => {
  it("grants health consent before saving flags and sends validated numbers", async () => {
    seedSession(false);
    let created = false;
    const fetchMock = mockFetch((url, init) => {
      if (url.pathname === "/api/v1/sessions/me/consent" && init.method === "POST") {
        return envelope({
          profile_id: "profile-1",
          has_household: false,
          consent: { version: "2026-11", health_consent_at: NOW },
          expires_at: FUTURE,
        });
      }
      if (url.pathname === "/api/v1/family/profile" && init.method === "POST") {
        created = true;
        return envelope(PROFILE);
      }
      if (url.pathname === "/api/v1/family/profile") {
        return created ? envelope(PROFILE) : problem(404, "NOT_FOUND", "No household yet.");
      }
      if (url.pathname === "/api/v1/family/preferences") {
        return envelope(PREFERENCES);
      }
      if (url.pathname === "/api/v1/family/recommendations") {
        return envelope({ items: [], limit: 20, offset: 0 });
      }
      return problem(500, "UNEXPECTED", `Unexpected route ${url.pathname}`);
    });
    const user = userEvent.setup();

    render(<FamilyView />);
    await screen.findByRole("heading", { name: "Create the household profile" });

    await user.type(screen.getByLabelText("Household name"), "Sharma household");
    await user.type(screen.getByLabelText("Latitude"), "28.6139");
    await user.type(screen.getByLabelText("Longitude"), "77.2090");
    await user.click(screen.getByRole("checkbox", { name: /Asthma or reactive airways/i }));
    await user.click(
      screen.getByRole("checkbox", {
        name: /I consent to storing the selected general health flags/i,
      }),
    );
    await user.click(screen.getByRole("button", { name: "Create family profile" }));

    await screen.findByText("Family profile created.");

    const consentIndex = fetchMock.mock.calls.findIndex(
      ([input]) => new URL(input.toString()).pathname === "/api/v1/sessions/me/consent",
    );
    const createIndex = fetchMock.mock.calls.findIndex(
      ([input, init]) =>
        new URL(input.toString()).pathname === "/api/v1/family/profile" && init?.method === "POST",
    );
    expect(consentIndex).toBeGreaterThanOrEqual(0);
    expect(createIndex).toBeGreaterThan(consentIndex);

    const createCall = fetchMock.mock.calls[createIndex];
    expect(JSON.parse(String(createCall?.[1]?.body))).toMatchObject({
      name: "Sharma household",
      lat: 28.6139,
      lon: 77.209,
      city: null,
      timezone: "Asia/Kolkata",
      members: [{ age_band: "18-59", health_flags: ["asthma"] }],
    });
  });

  it("rejects health flags without consent instead of silently dropping them", async () => {
    seedSession(false);
    mockFetch((url) => {
      if (url.pathname === "/api/v1/family/profile") {
        return problem(404, "NOT_FOUND", "No household yet.");
      }
      return problem(500, "UNEXPECTED", `Unexpected route ${url.pathname}`);
    });
    const user = userEvent.setup();

    render(<FamilyView />);
    await screen.findByRole("heading", { name: "Create the household profile" });

    await user.click(screen.getByRole("checkbox", { name: /Asthma or reactive airways/i }));
    await user.click(screen.getByRole("button", { name: "Create family profile" }));

    expect(
      await screen.findByText(/Grant health-data consent to save health flags, or remove them/),
    ).toBeVisible();
    expect(screen.getByLabelText("Household name")).toHaveAttribute("aria-invalid", "true");
  });
});

describe("empty states", () => {
  it("reports an unavailable family service without inventing a profile", async () => {
    seedSession();
    mockFetch(() => problem(503, "DATABASE_UNAVAILABLE", "Database unavailable."));

    render(<FamilyView />);

    expect(await screen.findByText("The household profile could not be loaded.")).toBeVisible();
    expect(screen.queryByText("Sharma household")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeVisible();
  });
});
