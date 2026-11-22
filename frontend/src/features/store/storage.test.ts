import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";

import {
  STORAGE_KEYS,
  readStored,
  removeStored,
  useStoredState,
  writeStored,
} from "@/features/store/storage";

const numberSchema = z.number();
const KEY = "saans.test.storage";

beforeEach(() => {
  window.localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("readStored", () => {
  it("returns the parsed value and null for every unusable case", () => {
    window.localStorage.setItem(KEY, JSON.stringify(42));
    expect(readStored(KEY, numberSchema)).toBe(42);

    expect(readStored("saans.test.missing", numberSchema)).toBeNull();

    window.localStorage.setItem(KEY, JSON.stringify("not a number"));
    expect(readStored(KEY, numberSchema)).toBeNull();

    window.localStorage.setItem(KEY, "{not json");
    expect(readStored(KEY, numberSchema)).toBeNull();
  });
});

describe("writeStored and removeStored", () => {
  it("persists, notifies listeners and removes", () => {
    const listener = vi.fn();
    window.addEventListener("saans:storage", listener);

    writeStored(KEY, { ok: true });
    expect(window.localStorage.getItem(KEY)).toBe('{"ok":true}');
    expect(listener).toHaveBeenCalledTimes(1);

    removeStored(KEY);
    expect(window.localStorage.getItem(KEY)).toBeNull();
    expect(listener).toHaveBeenCalledTimes(2);

    window.removeEventListener("saans:storage", listener);
  });
});

describe("useStoredState", () => {
  it("hydrates a valid stored value and supports functional updates", () => {
    window.localStorage.setItem(KEY, JSON.stringify(1));
    const { result } = renderHook(() => useStoredState(KEY, numberSchema, 0));

    expect(result.current.hydrated).toBe(true);
    expect(result.current.value).toBe(1);

    act(() => result.current.setValue((previous) => previous + 1));
    expect(result.current.value).toBe(2);
    expect(window.localStorage.getItem(KEY)).toBe("2");

    act(() => result.current.setValue(10));
    expect(window.localStorage.getItem(KEY)).toBe("10");

    act(() => result.current.reset());
    expect(result.current.value).toBe(0);
    expect(window.localStorage.getItem(KEY)).toBeNull();
  });

  it("falls back on malformed JSON and on a schema mismatch", () => {
    window.localStorage.setItem(KEY, "{broken");
    const malformed = renderHook(() => useStoredState(KEY, numberSchema, 7));
    expect(malformed.result.current.value).toBe(7);

    window.localStorage.setItem(KEY, JSON.stringify({ nope: true }));
    const mismatch = renderHook(() => useStoredState(KEY, numberSchema, 9));
    expect(mismatch.result.current.value).toBe(9);
  });

  it("returns a stable snapshot while the stored string is unchanged", () => {
    const objectSchema = z.object({ items: z.array(z.number()) });
    const fallback = { items: [] as number[] };
    window.localStorage.setItem(KEY, JSON.stringify({ items: [1] }));

    const first = renderHook(() => useStoredState(KEY, objectSchema, fallback));
    const firstValue = first.result.current.value;
    first.rerender();
    expect(first.result.current.value).toBe(firstValue);
  });

  it("keeps the default fallback when the browser refuses storage access", () => {
    const descriptor = Object.getOwnPropertyDescriptor(window, "localStorage");
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      get() {
        throw new Error("storage disabled");
      },
    });

    try {
      const { result } = renderHook(() => useStoredState(KEY, numberSchema, 5));
      expect(result.current.value).toBe(5);
      act(() => result.current.setValue(6));
      expect(result.current.value).toBe(5);
      expect(readStored(KEY, numberSchema)).toBeNull();
      expect(() => writeStored(KEY, 1)).not.toThrow();
    } finally {
      if (descriptor) {
        Object.defineProperty(window, "localStorage", descriptor);
      }
    }
  });
});

describe("storage keys", () => {
  it("keeps the documented namespace stable", () => {
    expect(Object.values(STORAGE_KEYS).every((key) => key.startsWith("saans.v1."))).toBe(true);
  });
});
