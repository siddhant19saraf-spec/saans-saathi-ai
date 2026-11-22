"use client";

import { useCallback, useSyncExternalStore } from "react";
import type { z } from "zod";

export const STORAGE_KEYS = {
  locations: "saans.v1.locations",
  routineActivities: "saans.v1.routine.activities",
  impactActivities: "saans.v1.impact.activities",
  indoorChecklist: "saans.v1.indoor.checklist",
  notificationPreferences: "saans.v1.settings.notifications",
  ecoPreferences: "saans.v1.eco.preferences",
} as const;

const STORAGE_EVENT = "saans:storage";

const emptySubscribe = () => () => {};

function storage(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

/**
 * Parsed snapshots are cached so `useSyncExternalStore` receives a stable
 * reference until the underlying raw string changes.
 */
const snapshotCache = new Map<string, { raw: string | null; value: unknown }>();

function snapshot<T>(key: string, schema: z.ZodType<T>, fallback: T): T {
  const store = storage();
  const raw = store ? store.getItem(key) : null;
  const cached = snapshotCache.get(key);
  if (cached && cached.raw === raw) {
    return cached.value as T;
  }

  let value = fallback;
  if (raw) {
    try {
      const parsed = schema.safeParse(JSON.parse(raw));
      if (parsed.success) {
        value = parsed.data;
      }
    } catch {
      value = fallback;
    }
  }
  snapshotCache.set(key, { raw, value });
  return value;
}

export function readStored<T>(key: string, schema: z.ZodType<T>): T | null {
  const store = storage();
  if (!store) {
    return null;
  }
  const raw = store.getItem(key);
  if (!raw) {
    return null;
  }
  try {
    const parsed = schema.safeParse(JSON.parse(raw));
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function notify() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(STORAGE_EVENT));
  }
}

export function writeStored(key: string, value: unknown): void {
  const store = storage();
  if (!store) {
    return;
  }
  store.setItem(key, JSON.stringify(value));
  notify();
}

export function removeStored(key: string): void {
  storage()?.removeItem(key);
  notify();
}

/** True after client hydration; false during server rendering and hydration. */
export function useHydrated(): boolean {
  return useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false,
  );
}

/**
 * Read and write a value that lives in localStorage.
 *
 * `useSyncExternalStore` keeps server and client markup identical during
 * hydration: the server snapshot is always the fallback and the stored value
 * is applied after hydration.
 */
export function useStoredState<T>(
  key: string,
  schema: z.ZodType<T>,
  fallback: T,
): {
  value: T;
  setValue: (next: T | ((previous: T) => T)) => void;
  hydrated: boolean;
  reset: () => void;
} {
  const subscribe = useCallback((onChange: () => void) => {
    window.addEventListener("storage", onChange);
    window.addEventListener(STORAGE_EVENT, onChange);
    return () => {
      window.removeEventListener("storage", onChange);
      window.removeEventListener(STORAGE_EVENT, onChange);
    };
  }, []);

  const value = useSyncExternalStore(
    subscribe,
    () => snapshot(key, schema, fallback),
    () => fallback,
  );
  const hydrated = useHydrated();

  const setValue = useCallback(
    (next: T | ((previous: T) => T)) => {
      const current = snapshot(key, schema, fallback);
      const resolved = typeof next === "function" ? (next as (value: T) => T)(current) : next;
      writeStored(key, resolved);
    },
    [key, schema, fallback],
  );

  const reset = useCallback(() => {
    removeStored(key);
  }, [key]);

  return { value, setValue, hydrated, reset };
}
