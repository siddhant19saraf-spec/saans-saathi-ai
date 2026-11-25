"use client";

import { useCallback } from "react";

import { STORAGE_KEYS, useStoredState } from "@/features/store/storage";

import { routineActivitiesSchema, type RoutineActivity } from "./schema";

const EMPTY: RoutineActivity[] = [];

export function useRoutineActivities() {
  const { value, setValue, hydrated } = useStoredState(
    STORAGE_KEYS.routineActivities,
    routineActivitiesSchema,
    EMPTY,
  );

  const add = useCallback(
    (activity: RoutineActivity) => {
      setValue((current) =>
        current.length >= 12 ? [...current.slice(1), activity] : [...current, activity],
      );
    },
    [setValue],
  );

  const remove = useCallback(
    (id: string) => {
      setValue((current) => current.filter((activity) => activity.id !== id));
    },
    [setValue],
  );

  const update = useCallback(
    (id: string, activity: RoutineActivity) => {
      setValue((current) =>
        current.map((item) => (item.id === id ? { ...activity, id } : item)),
      );
    },
    [setValue],
  );

  return { activities: value, add, remove, update, hydrated };
}
