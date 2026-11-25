import { useSyncExternalStore } from "react";

export const MOTION_STORAGE_KEY = "saans.v1.reduceMotion";

export function readMotionPreference(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(MOTION_STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

export function writeMotionPreference(reduce: boolean): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(MOTION_STORAGE_KEY, String(reduce));
  } catch {
    // Storage failures must not break the accessibility control.
  }
  applyMotionPreference(reduce);
  window.dispatchEvent(new CustomEvent("saans:motion-preference", { detail: reduce }));
}

export function applyMotionPreference(reduce: boolean): void {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.reduceMotion = String(reduce);
}

function subscribe(listener: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("storage", listener);
  window.addEventListener("saans:motion-preference", listener);
  return () => {
    window.removeEventListener("storage", listener);
    window.removeEventListener("saans:motion-preference", listener);
  };
}

/** Reads the in-app motion preference without setting state inside an effect. */
export function useMotionPreference(): { reduceMotion: boolean; setReduceMotion: (next: boolean) => void } {
  const reduceMotion = useSyncExternalStore(subscribe, readMotionPreference, () => false);
  return { reduceMotion, setReduceMotion: writeMotionPreference };
}
