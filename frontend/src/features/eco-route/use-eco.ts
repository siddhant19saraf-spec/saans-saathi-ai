"use client";

import { useCallback } from "react";

import { STORAGE_KEYS, useStoredState } from "@/features/store/storage";

import { DEFAULT_ECO_PREFERENCES, ecoPreferencesSchema, type EcoPreferences } from "./schema";

export function useEcoPreferences() {
  const { value, setValue, hydrated } = useStoredState(
    STORAGE_KEYS.ecoPreferences,
    ecoPreferencesSchema,
    DEFAULT_ECO_PREFERENCES,
  );

  const save = useCallback(
    (preferences: EcoPreferences) => {
      setValue(preferences);
    },
    [setValue],
  );

  return { preferences: value, save, hydrated };
}
