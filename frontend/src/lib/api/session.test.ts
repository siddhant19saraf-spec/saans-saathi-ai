import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  SESSION_EVENT,
  SESSION_STORAGE_KEY,
  clearStoredSession,
  readSessionToken,
  readStoredSession,
  writeStoredSession,
} from "@/lib/api/session";

const VALID = {
  token: "token-1",
  profileId: "profile-1",
  expiresAt: "2099-01-01T00:00:00Z",
  healthConsent: false,
};

beforeEach(() => {
  window.localStorage.clear();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("session storage", () => {
  it("returns null when no session exists", () => {
    expect(readStoredSession()).toBeNull();
    expect(readSessionToken()).toBeNull();
  });

  it("round-trips a session and emits a session event", () => {
    const listener = vi.fn();
    window.addEventListener(SESSION_EVENT, listener);

    writeStoredSession(VALID);

    expect(readStoredSession()).toEqual(VALID);
    expect(readSessionToken()).toBe("token-1");
    expect(listener).toHaveBeenCalledTimes(1);

    clearStoredSession();
    expect(readStoredSession()).toBeNull();
    expect(listener).toHaveBeenCalledTimes(2);

    window.removeEventListener(SESSION_EVENT, listener);
  });

  it("rejects malformed JSON and invalid session shapes", () => {
    window.localStorage.setItem(SESSION_STORAGE_KEY, "{oops");
    expect(readStoredSession()).toBeNull();

    window.localStorage.setItem(
      SESSION_STORAGE_KEY,
      JSON.stringify({ token: "", profileId: "p", expiresAt: "x", healthConsent: false }),
    );
    expect(readStoredSession()).toBeNull();
  });

  it("does not return an expired session", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2030-01-01T00:00:00Z"));
    window.localStorage.setItem(
      SESSION_STORAGE_KEY,
      JSON.stringify({ ...VALID, expiresAt: "2029-12-31T23:59:59Z" }),
    );

    expect(readStoredSession()).toBeNull();
  });

  it("keeps a stable object while the stored string is unchanged", () => {
    writeStoredSession(VALID);
    const first = readStoredSession();
    const second = readStoredSession();

    expect(first).toBe(second);
  });
});
