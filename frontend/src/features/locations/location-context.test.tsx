import { act, renderHook } from "@testing-library/react";
import type * as React from "react";
import { beforeEach, describe, expect, it } from "vitest";

import { LocationProvider, useLocations } from "@/features/locations/location-context";
import { STORAGE_KEYS } from "@/features/store/storage";

function wrapper({ children }: { children: React.ReactNode }) {
  return <LocationProvider>{children}</LocationProvider>;
}

function seedEight() {
  const items = Array.from({ length: 8 }, (_, index) => ({
    id: `loc-${index + 1}`,
    label: `Place ${index + 1}`,
    lat: 20 + index,
    lon: 75 + index,
    source: "manual" as const,
  }));
  window.localStorage.setItem(
    STORAGE_KEYS.locations,
    JSON.stringify({ items, activeId: "loc-1" }),
  );
}

beforeEach(() => {
  window.localStorage.clear();
});

describe("LocationProvider", () => {
  it("adds a location and makes it active", () => {
    const { result } = renderHook(() => useLocations(), { wrapper });

    act(() => {
      result.current.addLocation({
        label: "Home",
        lat: 28.6139,
        lon: 77.209,
        source: "manual",
      });
    });

    expect(result.current.locations).toHaveLength(1);
    expect(result.current.activeLocation?.label).toBe("Home");
  });

  it("reuses an existing coordinate instead of adding a duplicate", () => {
    const { result } = renderHook(() => useLocations(), { wrapper });

    let firstId = "";
    act(() => {
      firstId = result.current.addLocation({
        label: "Home",
        lat: 28.6139,
        lon: 77.209,
        source: "manual",
      }).id;
    });
    act(() => {
      result.current.addLocation({
        label: "Home again",
        lat: 28.61391,
        lon: 77.20901,
        source: "device",
      });
    });

    expect(result.current.locations).toHaveLength(1);
    expect(result.current.locations[0]!.label).toBe("Home");
    expect(result.current.activeLocation?.id).toBe(firstId);
  });

  it("keeps at most eight places, dropping the oldest", () => {
    seedEight();
    const { result } = renderHook(() => useLocations(), { wrapper });

    act(() => {
      result.current.addLocation({
        label: "Ninth",
        lat: 30,
        lon: 80,
        source: "map",
      });
    });

    expect(result.current.locations).toHaveLength(8);
    expect(result.current.locations[0]!.label).toBe("Place 2");
    expect(result.current.locations.at(-1)?.label).toBe("Ninth");
  });

  it("moves the active marker to the last saved place when the active one is removed", () => {
    const { result } = renderHook(() => useLocations(), { wrapper });

    act(() => {
      result.current.addLocation({ label: "One", lat: 20, lon: 75, source: "manual" });
      result.current.addLocation({ label: "Two", lat: 21, lon: 76, source: "manual" });
    });
    const active = result.current.activeLocation;
    expect(active?.label).toBe("Two");

    act(() => {
      result.current.removeLocation(active?.id ?? "");
    });

    expect(result.current.locations.map((item) => item.label)).toEqual(["One"]);
    expect(result.current.activeLocation?.label).toBe("One");
  });

  it("clears the active marker when the last place is removed", () => {
    const { result } = renderHook(() => useLocations(), { wrapper });

    act(() => {
      result.current.addLocation({ label: "Only", lat: 20, lon: 75, source: "manual" });
    });
    act(() => {
      result.current.removeLocation(result.current.locations[0]!.id);
    });

    expect(result.current.locations).toHaveLength(0);
    expect(result.current.activeLocation).toBeNull();
  });

  it("refuses to be used outside a provider", () => {
    expect(() => renderHook(() => useLocations())).toThrow(
      "useLocations must be used inside LocationProvider.",
    );
  });
});
