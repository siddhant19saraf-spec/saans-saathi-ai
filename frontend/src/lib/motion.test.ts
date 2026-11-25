import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  MOTION_STORAGE_KEY,
  applyMotionPreference,
  readMotionPreference,
  writeMotionPreference,
} from "./motion";

describe("motion preference helpers", () => {
  beforeEach(() => {
    window.localStorage.clear();
    delete document.documentElement.dataset.reduceMotion;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("defaults to motion enabled when nothing is stored", () => {
    expect(readMotionPreference()).toBe(false);
  });

  it("reads a stored reduce-motion preference", () => {
    window.localStorage.setItem(MOTION_STORAGE_KEY, "true");
    expect(readMotionPreference()).toBe(true);
  });

  it("falls back to motion enabled when storage throws", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("storage blocked");
    });
    expect(readMotionPreference()).toBe(false);
  });

  it("applies the preference to the document root dataset", () => {
    applyMotionPreference(true);
    expect(document.documentElement.dataset.reduceMotion).toBe("true");
    applyMotionPreference(false);
    expect(document.documentElement.dataset.reduceMotion).toBe("false");
  });

  it("persists and announces the preference", () => {
    const listener = vi.fn();
    window.addEventListener("saans:motion-preference", listener);

    writeMotionPreference(true);

    expect(window.localStorage.getItem(MOTION_STORAGE_KEY)).toBe("true");
    expect(document.documentElement.dataset.reduceMotion).toBe("true");
    expect(listener).toHaveBeenCalledTimes(1);
    const event = listener.mock.calls[0]?.[0] as CustomEvent<boolean>;
    expect(event.detail).toBe(true);

    window.removeEventListener("saans:motion-preference", listener);
  });

  it("still applies the preference when storage writes fail", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota exceeded");
    });

    expect(() => writeMotionPreference(true)).not.toThrow();
    expect(document.documentElement.dataset.reduceMotion).toBe("true");
  });
});
