"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { classifyApiFailure, useApiResource, type ApiFailure } from "@/features/api/resource";
import { useSession } from "@/features/session/use-session";

import {
  createFamilyProfile,
  deleteFamilyProfile,
  fetchFamilyPreferences,
  fetchFamilyProfile,
  fetchFamilyRecommendations,
  generateFamilyRecommendations,
  replaceFamilyPreferences,
  replaceFamilyProfile,
} from "./api";
import type {
  FamilyPreferencesResponse,
  FamilyProfile,
  FamilyRecommendationBatch,
  FamilyRecommendationList,
  PreferencesInput,
  ProfileInput,
} from "./schema";

export type LoadState =
  | { status: "idle" | "loading" | "success" }
  | { status: "error" | "unavailable"; message: string; code: string };

const HISTORY_PAGE = 20;

/**
 * Read-only profile lookup for surfaces outside the family page.
 *
 * It never creates a session: without a stored token there is no server
 * profile, and the caller shows its first-run state.
 */
export function useFamilyOverview() {
  const { session, hydrated } = useSession();
  const token = session?.token ?? null;
  const loader = useMemo(
    () => (token ? (signal: AbortSignal) => fetchFamilyProfile(signal) : null),
    [token],
  );
  const { state, retry } = useApiResource(loader);
  return {
    session,
    hydrated,
    profile: state.status === "success" ? state.data : null,
    state,
    retry,
  };
}

export type BusyAction = "profile" | "preferences" | "generate" | "delete" | null;

/**
 * Server-backed family workspace.
 *
 * The profile and preferences live in PostgreSQL under the anonymous session;
 * nothing is kept in localStorage except the session token itself. A missing
 * family profile is a first-run state, never an error.
 */
export function useFamilyWorkspace() {
  const { session, hydrated, start, grantHealthConsent, deleteSession, clear } = useSession();
  const [refresh, setRefresh] = useState(0);
  const [profile, setProfile] = useState<FamilyProfile | null>(null);
  const [profileState, setProfileState] = useState<LoadState>({ status: "idle" });
  const [preferences, setPreferences] = useState<FamilyPreferencesResponse | null>(null);
  const [preferencesState, setPreferencesState] = useState<LoadState>({ status: "idle" });
  const [batch, setBatch] = useState<FamilyRecommendationBatch | null>(null);
  const [history, setHistory] = useState<FamilyRecommendationList | null>(null);
  const [historyState, setHistoryState] = useState<LoadState>({ status: "idle" });
  const [busy, setBusy] = useState<BusyAction>(null);
  const [failure, setFailure] = useState<ApiFailure | null>(null);

  const token = session?.token ?? null;

  useEffect(() => {
    if (!hydrated) {
      return;
    }
    if (!token) {
      return;
    }

    const controller = new AbortController();

    async function load() {
      setProfileState({ status: "loading" });
      setFailure(null);
      try {
        const nextProfile = await fetchFamilyProfile(controller.signal);
        if (controller.signal.aborted) {
          return;
        }
        setProfile(nextProfile);
        setProfileState({ status: "success" });

        if (!nextProfile) {
          setPreferences(null);
          setPreferencesState({ status: "idle" });
          setHistory(null);
          setHistoryState({ status: "idle" });
          return;
        }
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }
        setProfileState(classifyApiFailure(error));
        setHistoryState({ status: "idle" });
        return;
      }

      setPreferencesState({ status: "loading" });
      try {
        const nextPreferences = await fetchFamilyPreferences(controller.signal);
        if (controller.signal.aborted) {
          return;
        }
        setPreferences(nextPreferences);
        setPreferencesState({ status: "success" });
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }
        setPreferencesState(classifyApiFailure(error));
      }

      setHistoryState({ status: "loading" });
      try {
        const page = await fetchFamilyRecommendations(controller.signal, {
          limit: HISTORY_PAGE,
          offset: 0,
        });
        if (controller.signal.aborted) {
          return;
        }
        setHistory(page);
        setHistoryState({ status: "success" });
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }
        setHistoryState(classifyApiFailure(error));
      }
    }

    void load();
    return () => controller.abort();
  }, [token, hydrated, refresh]);

  const reload = useCallback(() => setRefresh((value) => value + 1), []);

  const startSession = useCallback(
    async (healthConsent: boolean): Promise<string | null> => {
      try {
        await start(healthConsent);
        return null;
      } catch (error) {
        return classifyApiFailure(error).message;
      }
    },
    [start],
  );

  const saveProfile = useCallback(
    async (input: ProfileInput, options: { grantHealthConsent: boolean }) => {
      setBusy("profile");
      setFailure(null);
      try {
        if (options.grantHealthConsent && session && !session.healthConsent) {
          await grantHealthConsent();
        }
        const saved = profile
          ? await replaceFamilyProfile(input)
          : await createFamilyProfile(input);
        setProfile(saved);
        setProfileState({ status: "success" });
        setRefresh((value) => value + 1);
        return true;
      } catch (error) {
        setFailure(classifyApiFailure(error));
        return false;
      } finally {
        setBusy(null);
      }
    },
    [grantHealthConsent, profile, session],
  );

  const removeProfile = useCallback(async () => {
    setBusy("delete");
    setFailure(null);
    try {
      await deleteFamilyProfile();
      setProfile(null);
      setProfileState({ status: "success" });
      setPreferences(null);
      setPreferencesState({ status: "idle" });
      setHistory(null);
      setHistoryState({ status: "idle" });
      setBatch(null);
      return true;
    } catch (error) {
      setFailure(classifyApiFailure(error));
      return false;
    } finally {
      setBusy(null);
    }
  }, []);

  const savePreferences = useCallback(async (input: PreferencesInput) => {
    setBusy("preferences");
    setFailure(null);
    try {
      const saved = await replaceFamilyPreferences(input);
      setPreferences(saved);
      setPreferencesState({ status: "success" });
      return true;
    } catch (error) {
      setFailure(classifyApiFailure(error));
      return false;
    } finally {
      setBusy(null);
    }
  }, []);

  const generate = useCallback(async () => {
    setBusy("generate");
    setFailure(null);
    try {
      const result = await generateFamilyRecommendations();
      setBatch(result);
      const page = await fetchFamilyRecommendations(new AbortController().signal, {
        limit: HISTORY_PAGE,
        offset: 0,
      });
      setHistory(page);
      setHistoryState({ status: "success" });
      return true;
    } catch (error) {
      setFailure(classifyApiFailure(error));
      return false;
    } finally {
      setBusy(null);
    }
  }, []);

  const loadMoreHistory = useCallback(async () => {
    if (!history) {
      return;
    }
    setHistoryState({ status: "loading" });
    try {
      const page = await fetchFamilyRecommendations(new AbortController().signal, {
        limit: HISTORY_PAGE,
        offset: history.items.length,
      });
      setHistory({
        items: [...history.items, ...page.items],
        limit: page.limit,
        offset: page.offset,
      });
      setHistoryState({ status: "success" });
    } catch (error) {
      setHistoryState(classifyApiFailure(error));
    }
  }, [history]);

  const dismissFailure = useCallback(() => setFailure(null), []);

  const endSession = useCallback(async () => {
    setBusy("delete");
    setFailure(null);
    try {
      await deleteSession();
      return true;
    } catch (error) {
      setFailure(classifyApiFailure(error));
      return false;
    } finally {
      setBusy(null);
    }
  }, [deleteSession]);

  return {
    session,
    hydrated,
    startSession,
    profile,
    profileState,
    preferences,
    preferencesState,
    batch,
    history,
    historyState,
    busy,
    failure,
    dismissFailure,
    reload,
    saveProfile,
    removeProfile,
    savePreferences,
    generate,
    loadMoreHistory,
    endSession,
    clear,
    hasMoreHistory: history ? history.items.length >= history.limit : false,
  };
}
