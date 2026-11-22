"use client";

import { useCallback } from "react";

import { STORAGE_KEYS, useStoredState } from "@/features/store/storage";

import {
  DEFAULT_NOTIFICATION_PREFERENCES,
  notificationPreferencesSchema,
  type NotificationPreferences,
} from "./schema";

export function useNotificationPreferences() {
  const { value, setValue, hydrated } = useStoredState(
    STORAGE_KEYS.notificationPreferences,
    notificationPreferencesSchema,
    DEFAULT_NOTIFICATION_PREFERENCES,
  );

  const setPreference = useCallback(
    (key: keyof NotificationPreferences, enabled: boolean) => {
      setValue((current) => ({ ...current, [key]: enabled }));
    },
    [setValue],
  );

  return { preferences: value, setPreference, hydrated };
}
