"use client";

import { createContext, useCallback, useContext, useMemo } from "react";
import type * as React from "react";

import { STORAGE_KEYS, useStoredState } from "@/features/store/storage";

import { DEFAULT_LOCATIONS, locationsStateSchema, type SavedLocation } from "./schema";

type NewLocation = Omit<SavedLocation, "id">;

type LocationContextValue = {
  locations: SavedLocation[];
  activeLocation: SavedLocation | null;
  hydrated: boolean;
  addLocation: (location: NewLocation) => SavedLocation;
  removeLocation: (id: string) => void;
  setActiveLocation: (id: string) => void;
};

const LocationContext = createContext<LocationContextValue | null>(null);

const MAX_LOCATIONS = 8;

export function LocationProvider({ children }: { children: React.ReactNode }) {
  const { value, setValue, hydrated } = useStoredState(
    STORAGE_KEYS.locations,
    locationsStateSchema,
    DEFAULT_LOCATIONS,
  );

  const addLocation = useCallback(
    (location: NewLocation): SavedLocation => {
      const existing = value.items.find(
        (item) =>
          Math.abs(item.lat - location.lat) < 0.0001 && Math.abs(item.lon - location.lon) < 0.0001,
      );
      if (existing) {
        setValue((current) => ({ ...current, activeId: existing.id }));
        return existing;
      }

      const created: SavedLocation = {
        ...location,
        id:
          typeof crypto !== "undefined" && "randomUUID" in crypto
            ? crypto.randomUUID()
            : `loc-${Date.now()}`,
      };
      setValue((current) => {
        const items = [...current.items, created];
        return {
          items: items.length > MAX_LOCATIONS ? items.slice(-MAX_LOCATIONS) : items,
          activeId: created.id,
        };
      });
      return created;
    },
    [setValue, value.items],
  );

  const removeLocation = useCallback(
    (id: string) => {
      setValue((current) => {
        const items = current.items.filter((item) => item.id !== id);
        return {
          items,
          activeId: current.activeId === id ? (items.at(-1)?.id ?? null) : current.activeId,
        };
      });
    },
    [setValue],
  );

  const setActiveLocation = useCallback(
    (id: string) => {
      setValue((current) => ({ ...current, activeId: id }));
    },
    [setValue],
  );

  const activeLocation = useMemo(
    () => value.items.find((item) => item.id === value.activeId) ?? null,
    [value],
  );

  const contextValue = useMemo(
    () => ({
      locations: value.items,
      activeLocation,
      hydrated,
      addLocation,
      removeLocation,
      setActiveLocation,
    }),
    [value.items, activeLocation, hydrated, addLocation, removeLocation, setActiveLocation],
  );

  return <LocationContext.Provider value={contextValue}>{children}</LocationContext.Provider>;
}

export function useLocations(): LocationContextValue {
  const context = useContext(LocationContext);
  if (!context) {
    throw new Error("useLocations must be used inside LocationProvider.");
  }
  return context;
}
