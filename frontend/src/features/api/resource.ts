"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";

export type ResourceStatus = "idle" | "loading" | "success" | "unavailable" | "error";

export type ResourceState<T> =
  | { status: "idle" | "loading" }
  | { status: "success"; data: T }
  | { status: "unavailable" | "error"; message: string; code: string };

export type ApiFailure = {
  status: "unavailable" | "error";
  message: string;
  code: string;
};

/**
 * Classify a failed request. Missing or unconfigured services are not
 * application errors; they get their own state so the UI can say so.
 */
export function classifyApiFailure(error: unknown): ApiFailure {
  if (error instanceof ApiError) {
    if (error.status === 0) {
      return {
        status: "unavailable",
        message: "The API could not be reached. Check that the backend is running.",
        code: error.code,
      };
    }
    if (error.status === 404) {
      return {
        status: "unavailable",
        message: "This data service is not available in this build.",
        code: error.code,
      };
    }
    if (error.status === 401 || error.status === 403) {
      return {
        status: "unavailable",
        message: "Your session is missing or has expired. Start a new session to continue.",
        code: error.code,
      };
    }
    if (error.status === 503) {
      return {
        status: "unavailable",
        message: "The data service is temporarily unavailable. Try again shortly.",
        code: error.code,
      };
    }
    return { status: "error", message: error.message, code: error.code };
  }

  return {
    status: "error",
    message: "The response could not be processed.",
    code: "UNEXPECTED_ERROR",
  };
}

type Loader<T> = (signal: AbortSignal) => Promise<T>;

type Settled<T> = {
  loader: Loader<T>;
  attempt: number;
  state: ResourceState<T>;
};

/**
 * Run a loader and expose loading, success, unavailable and error states.
 * The loader must be memoised with useCallback by the caller. While a new
 * loader or retry has not settled, the derived state is `loading`, so stale
 * results are never shown for a different location.
 */
export function useApiResource<T>(loader: Loader<T> | null) {
  const [settled, setSettled] = useState<Settled<T> | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!loader) {
      return;
    }

    const controller = new AbortController();
    let active = true;

    loader(controller.signal)
      .then((data) => {
        if (active) {
          setSettled({ loader, attempt, state: { status: "success", data } });
        }
      })
      .catch((error: unknown) => {
        if (!active || controller.signal.aborted) {
          return;
        }
        setSettled({ loader, attempt, state: classifyApiFailure(error) });
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [loader, attempt]);

  const retry = useCallback(() => setAttempt((value) => value + 1), []);

  const state: ResourceState<T> = !loader
    ? { status: "idle" }
    : settled && settled.loader === loader && settled.attempt === attempt
      ? settled.state
      : { status: "loading" };

  return { state, retry };
}
