"use client";

import { useMemo } from "react";

import { apiData } from "@/features/api/client";
import { useApiResource } from "@/features/api/resource";
import { roundCoordinate, type SavedLocation } from "@/features/locations/schema";

import {
  airCurrentSchema,
  airForecastSchema,
  airHistorySchema,
  airStationsSchema,
  locationSearchResultsSchema,
  providerHealthListSchema,
  type AirCurrent,
  type AirForecast,
  type AirHistory,
  type AirStations,
  type LocationSearchResults,
  type ProviderHealthList,
} from "./schemas";

const BASE = "/api/v1/air-quality";

export type DataProvider = "open-meteo" | "openaq" | "cpcb";

function coordinates(location: { lat: number; lon: number }): string {
  return `lat=${roundCoordinate(location.lat)}&lon=${roundCoordinate(location.lon)}`;
}

function providerParam(provider?: DataProvider): string {
  return provider ? `&provider=${provider}` : "";
}

export function fetchAirCurrent(
  location: { lat: number; lon: number },
  signal: AbortSignal,
  provider?: DataProvider,
): Promise<AirCurrent> {
  return apiData(
    `${BASE}/current?${coordinates(location)}${providerParam(provider)}`,
    airCurrentSchema,
    { signal },
  );
}

export function fetchAirForecast(
  location: { lat: number; lon: number },
  hours: 24 | 48 | 72,
  signal: AbortSignal,
  provider?: DataProvider,
): Promise<AirForecast> {
  return apiData(
    `${BASE}/forecast?${coordinates(location)}&hours=${hours}${providerParam(provider)}`,
    airForecastSchema,
    { signal },
  );
}

export function fetchAirHistory(
  location: { lat: number; lon: number },
  days: number,
  signal: AbortSignal,
  provider?: DataProvider,
): Promise<AirHistory> {
  return apiData(
    `${BASE}/history?${coordinates(location)}&days=${days}${providerParam(provider)}`,
    airHistorySchema,
    { signal },
  );
}

export function fetchAirStations(
  location: { lat: number; lon: number },
  signal: AbortSignal,
  options: { provider?: DataProvider; radiusKm?: number; limit?: number } = {},
): Promise<AirStations> {
  const params = new URLSearchParams({
    lat: String(roundCoordinate(location.lat)),
    lon: String(roundCoordinate(location.lon)),
  });
  if (options.provider) params.set("provider", options.provider);
  if (options.radiusKm) params.set("radius_km", String(options.radiusKm));
  if (options.limit) params.set("limit", String(options.limit));
  return apiData(`${BASE}/stations?${params.toString()}`, airStationsSchema, { signal });
}

export function fetchProviderHealth(signal: AbortSignal): Promise<ProviderHealthList> {
  return apiData(`${BASE}/providers/health`, providerHealthListSchema, { signal });
}

export function fetchLocationSearch(
  query: string,
  signal: AbortSignal,
  options: { limit?: number; countryCode?: string } = {},
): Promise<LocationSearchResults> {
  const params = new URLSearchParams({ q: query });
  if (options.limit) params.set("limit", String(options.limit));
  if (options.countryCode) params.set("country_code", options.countryCode);
  return apiData(`/api/v1/locations/search?${params.toString()}`, locationSearchResultsSchema, {
    signal,
  });
}

export function useAirCurrent(location: SavedLocation | null, provider?: DataProvider) {
  const loader = useMemo(
    () => (location ? (signal: AbortSignal) => fetchAirCurrent(location, signal, provider) : null),
    [location, provider],
  );
  return useApiResource(loader);
}

export function useAirForecast(
  location: SavedLocation | null,
  hours: 24 | 48 | 72 = 24,
  provider?: DataProvider,
) {
  const loader = useMemo(
    () =>
      location
        ? (signal: AbortSignal) => fetchAirForecast(location, hours, signal, provider)
        : null,
    [location, hours, provider],
  );
  return useApiResource(loader);
}

export function useAirHistory(location: SavedLocation | null, days = 7, provider?: DataProvider) {
  const loader = useMemo(
    () =>
      location ? (signal: AbortSignal) => fetchAirHistory(location, days, signal, provider) : null,
    [location, days, provider],
  );
  return useApiResource(loader);
}

export function useProviderHealth() {
  const loader = useMemo(() => (signal: AbortSignal) => fetchProviderHealth(signal), []);
  return useApiResource(loader);
}
