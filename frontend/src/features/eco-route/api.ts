import { z } from "zod";

import { apiData } from "@/features/api/client";
import type { SavedLocation } from "@/features/locations/schema";

import type { TravelMode } from "./schema";

const routeSchema = z.object({
  distance_km: z.number().nonnegative(),
  duration_min: z.number().nonnegative(),
  source: z.string(),
  is_estimate: z.boolean(),
});

const modeComparisonSchema = z.object({
  mode: z.string(),
  co2e_kg: z.number().nonnegative().nullable(),
  exposure_index: z.number().nullable(),
  duration_min: z.number().nonnegative().nullable(),
  recommended_for: z.array(z.string()),
});

export const ecoRouteComparisonSchema = z.object({
  route: routeSchema,
  modes: z.array(modeComparisonSchema),
  tradeoff_note: z.string().nullable(),
  assumptions: z.array(
    z.object({
      key: z.string(),
      value: z.union([z.number(), z.string()]),
      source: z.string(),
    }),
  ),
});

export type EcoRouteComparison = z.infer<typeof ecoRouteComparisonSchema>;
export type EcoRouteMode = z.infer<typeof modeComparisonSchema>;

export type EcoRouteRequest = {
  origin: { lat: number; lon: number };
  destination: { lat: number; lon: number };
  modes: TravelMode[];
};

export function compareEcoRoute(
  request: EcoRouteRequest,
  signal: AbortSignal,
): Promise<EcoRouteComparison> {
  return apiData("/api/v1/ecoroute/compare", ecoRouteComparisonSchema, {
    method: "POST",
    body: request,
    signal,
  });
}

export function originFromLocation(
  location: SavedLocation | null,
): { lat: number; lon: number } | null {
  return location ? { lat: location.lat, lon: location.lon } : null;
}
