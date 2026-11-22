"use client";

import { useCallback, useSyncExternalStore } from "react";
import { z } from "zod";

import { useHydrated } from "@/features/store/storage";
import { apiData, apiDelete } from "@/features/api/client";
import {
  SESSION_EVENT,
  clearStoredSession,
  readStoredSession,
  writeStoredSession,
  type StoredSession,
} from "@/lib/api/session";

/** Version tag stored with the consent decision; bump when the policy changes. */
export const CONSENT_VERSION = "2026-11";

const sessionCreatedSchema = z.object({
  token: z.string().min(1),
  expires_at: z.string().min(1),
  profile_id: z.string().min(1),
});

const sessionInfoSchema = z.object({
  profile_id: z.string().min(1),
  has_household: z.boolean(),
  consent: z.object({
    version: z.string(),
    health_consent_at: z.string().nullable(),
  }),
  expires_at: z.string().min(1),
});

function subscribe(onChange: () => void): () => void {
  window.addEventListener("storage", onChange);
  window.addEventListener(SESSION_EVENT, onChange);
  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener(SESSION_EVENT, onChange);
  };
}

/**
 * Anonymous session state shared by every family surface.
 *
 * Starting a session is an explicit user action: the backend then stores a
 * household profile for this browser. Health-flag storage is a separate
 * consent that can be granted later without losing the profile.
 */
export function useSession() {
  const session = useSyncExternalStore(subscribe, readStoredSession, () => null);
  const hydrated = useHydrated();

  const start = useCallback(async (healthConsent: boolean): Promise<StoredSession> => {
    const created = await apiData("/api/v1/sessions", sessionCreatedSchema, {
      method: "POST",
      body: { consent_version: CONSENT_VERSION, health_consent: healthConsent },
    });
    const stored: StoredSession = {
      token: created.token,
      profileId: created.profile_id,
      expiresAt: created.expires_at,
      healthConsent,
    };
    writeStoredSession(stored);
    return stored;
  }, []);

  const grantHealthConsent = useCallback(async (): Promise<void> => {
    const info = await apiData("/api/v1/sessions/me/consent", sessionInfoSchema, {
      method: "POST",
      body: { health_consent: true },
    });
    const current = readStoredSession();
    if (current) {
      writeStoredSession({
        ...current,
        healthConsent: info.consent.health_consent_at !== null,
      });
    }
  }, []);

  const deleteSession = useCallback(async (): Promise<void> => {
    await apiDelete("/api/v1/sessions/me");
    clearStoredSession();
  }, []);

  const clear = useCallback(() => {
    clearStoredSession();
  }, []);

  return { session, hydrated, start, grantHealthConsent, deleteSession, clear };
}
