"use client";

import { useCallback } from "react";

import { STORAGE_KEYS, useStoredState } from "@/features/store/storage";

import { indoorChecklistSchema, type IndoorChecklist } from "./schema";

const EMPTY: IndoorChecklist = {};

export function useIndoorChecklist() {
  const { value, setValue, hydrated, reset } = useStoredState(
    STORAGE_KEYS.indoorChecklist,
    indoorChecklistSchema,
    EMPTY,
  );

  const toggle = useCallback(
    (id: string, checked: boolean) => {
      setValue((current) => ({ ...current, [id]: checked }));
    },
    [setValue],
  );

  const completed = Object.values(value).filter(Boolean).length;

  return { checklist: value, toggle, completed, reset, hydrated };
}
