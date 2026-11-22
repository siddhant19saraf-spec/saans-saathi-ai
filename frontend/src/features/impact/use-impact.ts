"use client";

import { useCallback } from "react";

import { STORAGE_KEYS, useStoredState } from "@/features/store/storage";

import { impactActivitiesSchema, type ImpactActivity } from "./schema";

const EMPTY: ImpactActivity[] = [];

export function useImpactActivities() {
  const { value, setValue, hydrated } = useStoredState(
    STORAGE_KEYS.impactActivities,
    impactActivitiesSchema,
    EMPTY,
  );

  const add = useCallback(
    (activity: ImpactActivity) => {
      setValue((current) => [activity, ...current].slice(0, 200));
    },
    [setValue],
  );

  const remove = useCallback(
    (id: string) => {
      setValue((current) => current.filter((activity) => activity.id !== id));
    },
    [setValue],
  );

  return { activities: value, add, remove, hydrated };
}
