"use client";

import { useEffect } from "react";

import { applyMotionPreference, readMotionPreference } from "@/lib/motion";

export function MotionPreference() {
  useEffect(() => {
    applyMotionPreference(readMotionPreference());

    function onStorage(event: StorageEvent) {
      if (event.key === "saans.v1.reduceMotion") {
        applyMotionPreference(event.newValue === "true");
      }
    }

    function onPreference(event: Event) {
      const detail = (event as CustomEvent<boolean>).detail;
      applyMotionPreference(Boolean(detail));
    }

    window.addEventListener("storage", onStorage);
    window.addEventListener("saans:motion-preference", onPreference);
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("saans:motion-preference", onPreference);
    };
  }, []);

  return null;
}
