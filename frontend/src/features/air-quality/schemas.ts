import { z } from "zod";

import { aqiCategories } from "./severity";

const nullableNumber = z.number().nullable();

export const sourceTypeSchema = z.enum([
  "ground_observation",
  "model_forecast",
  "historical_observation",
]);

const coordinatesSchema = z.object({
  lat: z.number(),
  lon: z.number(),
});

export const stationSchema = z.object({
  id: z.string(),
  name: z.string(),
  provider: z.string(),
  latitude: z.number(),
  longitude: z.number(),
  distance_km: z.number().nullable().optional(),
  timezone: z.string().nullable().optional(),
  is_monitor: z.boolean().nullable().optional(),
});

export const airLocationSchema = z.object({
  requested: coordinatesSchema,
  resolved: coordinatesSchema.nullable().optional(),
  timezone: z.string().nullable().optional(),
});

export const airReadingSchema = z.object({
  pm2_5: nullableNumber,
  pm10: nullableNumber,
  co_ug_m3: nullableNumber,
  no2_ug_m3: nullableNumber,
  so2_ug_m3: nullableNumber,
  o3_ug_m3: nullableNumber,
  dust_ug_m3: nullableNumber.optional(),
});

export const averagingBreakdownSchema = z.object({
  pollutant: z.string(),
  window: z.string(),
  hours: z.number().int(),
  valid_hours: z.number().int(),
  required_hours: z.number().int(),
  method: z.string(),
  complete: z.boolean(),
});

export const cpcbAqiSchema = z.object({
  value: z.number().min(0).max(500),
  category: z.enum(aqiCategories),
  dominant_pollutant: z.string(),
  method: z.string(),
  coverage: z.array(z.string()),
  partial: z.boolean(),
  basis: z.string().optional(),
  averaging: z.array(averagingBreakdownSchema).optional(),
  source: z.string().optional(),
});

export const provenanceSchema = z.object({
  provider: z.string(),
  kind: z.string(),
  source_type: sourceTypeSchema.optional(),
  model: z.string().optional(),
  observed_at: z.string().nullable(),
  fetched_at: z.string(),
  age_minutes: z.number(),
  freshness: z.enum(["fresh", "stale"]).optional(),
  stale: z.boolean(),
  station: stationSchema.nullable().optional(),
  attribution: z.array(z.string()),
});

export const airCurrentSchema = z.object({
  location: airLocationSchema,
  reading: airReadingSchema,
  cpcb_aqi: cpcbAqiSchema.nullable(),
  aqi_unavailable_reason: z.string().nullable().optional(),
  provider_aqi: z
    .object({
      us: z.number().nullable(),
      european: z.number().nullable(),
      note: z.string(),
    })
    .optional(),
  provenance: provenanceSchema,
});

export const forecastPointSchema = z.object({
  time: z.string(),
  pm2_5: z.number().nullable().optional(),
  pm10: z.number().nullable().optional(),
  no2_ug_m3: z.number().nullable().optional(),
  o3_ug_m3: z.number().nullable().optional(),
  co_ug_m3: z.number().nullable().optional(),
  so2_ug_m3: z.number().nullable().optional(),
});

export const airForecastSchema = z.object({
  location: airLocationSchema.optional(),
  hourly: z.array(forecastPointSchema),
  provenance: provenanceSchema.optional(),
});

export const historyPointSchema = z.object({
  date: z.string(),
  pm2_5: z.number().nullable().optional(),
  pm10: z.number().nullable().optional(),
});

export const airHistorySchema = z.object({
  daily: z.array(historyPointSchema),
  provenance: provenanceSchema.optional(),
});

export const airStationsSchema = z.object({
  provider: z.string(),
  radius_km: z.number().int(),
  stations: z.array(stationSchema),
  fetched_at: z.string(),
  attribution: z.array(z.string()),
});

export const providerHealthSchema = z.object({
  name: z.string(),
  status: z.enum(["ok", "degraded", "unavailable", "not_configured"]),
  configured: z.boolean(),
  source_type: sourceTypeSchema,
  supports_forecast: z.boolean(),
  supports_history: z.boolean(),
  supports_stations: z.boolean(),
  circuit_state: z.string(),
  attribution: z.array(z.string()),
  detail: z.string(),
});

export const providerHealthListSchema = z.object({
  providers: z.array(providerHealthSchema),
});

export const locationSearchResultSchema = z.object({
  id: z.string(),
  name: z.string(),
  latitude: z.number(),
  longitude: z.number(),
  country: z.string().nullable().optional(),
  country_code: z.string().nullable().optional(),
  admin1: z.string().nullable().optional(),
  timezone: z.string().nullable().optional(),
  population: z.number().nullable().optional(),
});

export const locationSearchResultsSchema = z.object({
  query: z.string(),
  results: z.array(locationSearchResultSchema),
  attribution: z.array(z.string()),
});

export type AirCurrent = z.infer<typeof airCurrentSchema>;
export type AirReading = z.infer<typeof airReadingSchema>;
export type CpcbAqi = z.infer<typeof cpcbAqiSchema>;
export type AveragingBreakdown = z.infer<typeof averagingBreakdownSchema>;
export type AirProvenance = z.infer<typeof provenanceSchema>;
export type AirForecast = z.infer<typeof airForecastSchema>;
export type AirHistory = z.infer<typeof airHistorySchema>;
export type AirStations = z.infer<typeof airStationsSchema>;
export type ForecastPoint = z.infer<typeof forecastPointSchema>;
export type Station = z.infer<typeof stationSchema>;
export type SourceType = z.infer<typeof sourceTypeSchema>;
export type ProviderHealth = z.infer<typeof providerHealthSchema>;
export type ProviderHealthList = z.infer<typeof providerHealthListSchema>;
export type LocationSearchResult = z.infer<typeof locationSearchResultSchema>;
export type LocationSearchResults = z.infer<typeof locationSearchResultsSchema>;
