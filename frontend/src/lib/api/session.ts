import { z } from "zod";

/**
 * Anonymous session storage.
 *
 * The backend issues one opaque bearer token and stores only its SHA-256
 * digest. The browser keeps the token in localStorage so it can be sent with
 * requests; no name, email or phone number is involved.
 */
export const SESSION_STORAGE_KEY = "saans.v1.session";
export const SESSION_EVENT = "saans:session";

export const storedSessionSchema = z.object({
  token: z.string().min(1),
  profileId: z.string().min(1),
  expiresAt: z.string().min(1),
  healthConsent: z.boolean(),
});

export type StoredSession = z.infer<typeof storedSessionSchema>;

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

function notify() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(SESSION_EVENT));
  }
}

// useSyncExternalStore compares snapshots with Object.is, so the parsed value
// must keep a stable reference until the stored string changes.
const snapshotCache = new Map<string, { raw: string | null; value: StoredSession | null }>();

export function readStoredSession(): StoredSession | null {
  const store = storage();
  if (!store) {
    return null;
  }
  const raw = store.getItem(SESSION_STORAGE_KEY);
  const cached = snapshotCache.get(SESSION_STORAGE_KEY);
  if (!cached || cached.raw !== raw) {
    let value: StoredSession | null = null;
    if (raw) {
      try {
        const parsed = storedSessionSchema.safeParse(JSON.parse(raw));
        value = parsed.success ? parsed.data : null;
      } catch {
        value = null;
      }
    }
    snapshotCache.set(SESSION_STORAGE_KEY, { raw, value });
  }

  const value = snapshotCache.get(SESSION_STORAGE_KEY)?.value ?? null;
  if (value && Date.parse(value.expiresAt) <= Date.now()) {
    return null;
  }
  return value;
}

export function readSessionToken(): string | null {
  return readStoredSession()?.token ?? null;
}

export function writeStoredSession(session: StoredSession): void {
  storage()?.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
  notify();
}

export function clearStoredSession(): void {
  storage()?.removeItem(SESSION_STORAGE_KEY);
  notify();
}
