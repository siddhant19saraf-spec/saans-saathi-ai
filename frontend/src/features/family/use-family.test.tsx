import { renderHook, act, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type {
  FamilyPreferencesResponse,
  FamilyProfile,
  FamilyRecommendationBatch,
  FamilyRecommendationList,
} from "./schema";

const api = vi.hoisted(() => ({
  fetchFamilyProfile: vi.fn(),
  createFamilyProfile: vi.fn(),
  replaceFamilyProfile: vi.fn(),
  deleteFamilyProfile: vi.fn(),
  fetchFamilyPreferences: vi.fn(),
  replaceFamilyPreferences: vi.fn(),
  fetchFamilyRecommendations: vi.fn(),
  generateFamilyRecommendations: vi.fn(),
}));

vi.mock("./api", () => api);

const sessionState = vi.hoisted(() => {
  const state: {
    session: null | { token: string; expiresAt: string; healthConsent: boolean };
    hydrated: boolean;
    start: ReturnType<typeof vi.fn>;
    grantHealthConsent: ReturnType<typeof vi.fn>;
    deleteSession: ReturnType<typeof vi.fn>;
    clear: ReturnType<typeof vi.fn>;
  } = {
    session: null,
    hydrated: true,
    start: vi.fn(),
    grantHealthConsent: vi.fn(),
    deleteSession: vi.fn(),
    clear: vi.fn(),
  };
  return state;
});

vi.mock("@/features/session/use-session", () => ({
  useSession: () => sessionState,
}));

import { useFamilyWorkspace } from "./use-family";

const PROFILE = {
  id: "hh-1",
  name: "Sharma household",
  size: 1,
  lat: 28.6,
  lon: 77.2,
  city: null,
  timezone: "Asia/Kolkata",
  dwelling: "apartment_upper",
  cooking_fuel: "lpg",
  has_purifier: false,
  purifier_cadr: null,
  room_area_m2: null,
  ceiling_m: null,
  members: [],
  has_children: false,
  has_older_adults: false,
  has_health_flags: false,
  created_at: "2026-11-19T08:00:00Z",
  updated_at: "2026-11-19T08:00:00Z",
} as FamilyProfile;

const PREFERENCES = {
  household_id: "hh-1",
  locale: "en-IN",
  activity_windows: [],
  alert_threshold_aqi: 150,
  transport_mode: "mixed",
  notifications_enabled: true,
  notify_alerts: true,
  notify_daily_summary: false,
  quiet_hours_start: null,
  quiet_hours_end: null,
  created_at: "2026-11-19T08:00:00Z",
  updated_at: "2026-11-19T08:00:00Z",
} as FamilyPreferencesResponse;

const BATCH = {
  household_id: "hh-1",
  generated_at: "2026-11-19T08:00:00Z",
  rules_version: "v1",
  pollution_context: {},
  recommendations: [],
  ai_explanation: { status: "unavailable", text: null, model: null, reason: null },
  disclaimer: "General guidance only.",
} as unknown as FamilyRecommendationBatch;

function page(items = 1, limit = 20): FamilyRecommendationList {
  return { items: Array.from({ length: items }, () => ({})), limit, offset: 0 } as FamilyRecommendationList;
}

beforeEach(() => {
  sessionState.session = null;
  sessionState.hydrated = true;
  sessionState.start.mockReset();
  sessionState.grantHealthConsent.mockReset().mockResolvedValue(undefined);
  sessionState.deleteSession.mockReset().mockResolvedValue(undefined);
  sessionState.clear.mockReset();
  for (const fn of Object.values(api)) {
    fn.mockReset();
  }
  api.fetchFamilyProfile.mockResolvedValue(PROFILE);
  api.fetchFamilyPreferences.mockResolvedValue(PREFERENCES);
  api.fetchFamilyRecommendations.mockResolvedValue(page());
  api.createFamilyProfile.mockResolvedValue(PROFILE);
  api.replaceFamilyProfile.mockResolvedValue(PROFILE);
  api.replaceFamilyPreferences.mockResolvedValue(PREFERENCES);
  api.deleteFamilyProfile.mockResolvedValue(undefined);
  api.generateFamilyRecommendations.mockResolvedValue(BATCH);
});

describe("useFamilyWorkspace mutations - profile creation", () => {
  it("creates a profile when starting a new session", async () => {
    const { result } = renderHook(() => useFamilyWorkspace());
    await waitFor(() => expect(result.current.profileState.status).toBe("idle"));

    act(() => {
      result.current.startSession(false).then(() => {});
    });

    expect(result.current.profile).toBeNull();

    await act(async () => {
      await expect(
        result.current.saveProfile(
          { name: "Sharma household" } as never,
          { grantHealthConsent: true },
        ),
      ).resolves.toBe(true);
    });

    expect(result.current.profile?.id).toBe("hh-1");
    expect(result.current.profile?.name).toBe("Sharma household");
    expect(api.createFamilyProfile).toHaveBeenCalledTimes(1);
  });

  it("creates a profile and completes the workflow when consent is requested", async () => {
    const { result } = renderHook(() => useFamilyWorkspace());
    await waitFor(() => expect(result.current.profileState.status).toBe("idle"));

    await act(async () => {
      await expect(
        result.current.saveProfile(
          { name: "Sharma household" } as never,
          { grantHealthConsent: true },
        ),
      ).resolves.toBe(true);
    });

    expect(result.current.profile?.id).toBe("hh-1");
    expect(result.current.profile?.name).toBe("Sharma household");
    expect(api.createFamilyProfile).toHaveBeenCalledTimes(1);
  });
});