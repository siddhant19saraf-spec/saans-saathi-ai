"use client";

import { apiData, apiDelete } from "@/features/api/client";
import { ApiError } from "@/lib/api/client";

import {
  familyProfileSchema,
  familyRecommendationSchema,
  preferencesResponseSchema,
  recommendationBatchSchema,
  recommendationListSchema,
  type FamilyPreferencesResponse,
  type FamilyProfile,
  type FamilyRecommendation,
  type FamilyRecommendationBatch,
  type FamilyRecommendationList,
  type PreferencesInput,
  type ProfileInput,
} from "./schema";

const BASE = "/api/v1/family";

/** A missing profile is a normal first-run state, not a service failure. */
export async function fetchFamilyProfile(signal: AbortSignal): Promise<FamilyProfile | null> {
  try {
    return await apiData(`${BASE}/profile`, familyProfileSchema, { signal });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export function createFamilyProfile(
  input: ProfileInput,
  signal?: AbortSignal,
): Promise<FamilyProfile> {
  return apiData(`${BASE}/profile`, familyProfileSchema, {
    method: "POST",
    body: input,
    signal,
  });
}

export function replaceFamilyProfile(
  input: ProfileInput,
  signal?: AbortSignal,
): Promise<FamilyProfile> {
  return apiData(`${BASE}/profile`, familyProfileSchema, {
    method: "PUT",
    body: input,
    signal,
  });
}

export function deleteFamilyProfile(signal?: AbortSignal): Promise<void> {
  return apiDelete(`${BASE}/profile`, { signal });
}

export function fetchFamilyPreferences(signal: AbortSignal): Promise<FamilyPreferencesResponse> {
  return apiData(`${BASE}/preferences`, preferencesResponseSchema, { signal });
}

export function replaceFamilyPreferences(
  input: PreferencesInput,
  signal?: AbortSignal,
): Promise<FamilyPreferencesResponse> {
  return apiData(`${BASE}/preferences`, preferencesResponseSchema, {
    method: "PUT",
    body: input,
    signal,
  });
}

export function generateFamilyRecommendations(
  signal?: AbortSignal,
): Promise<FamilyRecommendationBatch> {
  return apiData(`${BASE}/recommendations/generate`, recommendationBatchSchema, {
    method: "POST",
    signal,
  });
}

export function fetchFamilyRecommendations(
  signal: AbortSignal,
  options: { limit?: number; offset?: number } = {},
): Promise<FamilyRecommendationList> {
  const params = new URLSearchParams({
    limit: String(options.limit ?? 20),
    offset: String(options.offset ?? 0),
  });
  return apiData(`${BASE}/recommendations?${params.toString()}`, recommendationListSchema, {
    signal,
  });
}

export function fetchFamilyRecommendation(
  recommendationId: string,
  signal: AbortSignal,
): Promise<FamilyRecommendation> {
  return apiData(
    `${BASE}/recommendations/${encodeURIComponent(recommendationId)}`,
    familyRecommendationSchema,
    { signal },
  );
}
