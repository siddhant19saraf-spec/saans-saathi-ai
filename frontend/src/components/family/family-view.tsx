"use client";

import {
  CheckCircle2,
  History,
  Lock,
  Play,
  RefreshCw,
  Sparkles,
  Trash2,
  Users,
} from "lucide-react";
import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator, Skeleton } from "@/components/ui/feedback";
import { useFamilyWorkspace } from "@/features/family/use-family";
import {
  ACTIVITY_LABELS,
  AGE_BAND_OPTIONS,
  HEALTH_FLAG_LABELS,
  type FamilyProfile,
  type FamilyRecommendationBatch,
} from "@/features/family/schema";
import { formatDateTime, titleCase } from "@/lib/format";

import { HouseholdForm } from "./household-form";
import { PreferencesForm } from "./preferences-form";
import { RecommendationCard } from "./recommendation-card";
import { SessionGate } from "./session-gate";

export function FamilyView() {
  const workspace = useFamilyWorkspace();
  const [notice, setNotice] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [confirmDeleteProfile, setConfirmDeleteProfile] = useState(false);
  const [confirmEndSession, setConfirmEndSession] = useState(false);

  const {
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
    hasMoreHistory,
  } = workspace;

  if (!hydrated) {
    return (
      <div aria-busy="true" aria-live="polite" className="space-y-4">
        <span className="sr-only">Loading family intelligence</span>
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (!session) {
    return (
      <SessionGate
        busy={starting}
        onStart={async (healthConsent) => {
          setStarting(true);
          const message = await startSession(healthConsent);
          setStarting(false);
          if (!message) {
            setNotice("Anonymous session started. Create the household profile below.");
          }
          return message;
        }}
      />
    );
  }

  if ((profileState.status === "idle" || profileState.status === "loading") && !profile) {
    return (
      <div aria-busy="true" aria-live="polite" className="space-y-4">
        <span className="sr-only">Loading household profile</span>
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (profileState.status === "error" || profileState.status === "unavailable") {
    return (
      <div className="space-y-4">
        <Alert variant="error">
          <AlertDescription>
            <p className="font-semibold">The household profile could not be loaded.</p>
            <p>{profileState.message}</p>
          </AlertDescription>
        </Alert>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" onClick={reload}>
            <RefreshCw className="size-4" aria-hidden="true" />
            Try again
          </Button>
          <Button type="button" variant="ghost" onClick={clear}>
            Start a new session
          </Button>
        </div>
      </div>
    );
  }

  const latestGeneratedAt = batch?.generated_at ?? null;
  const batchIds = new Set(batch?.recommendations.map((item) => item.recommendation_id) ?? []);
  const storedItems = history?.items.filter((item) => !batchIds.has(item.recommendation_id)) ?? [];
  const noActivities = preferences !== null && preferences.activity_windows.length === 0;

  return (
    <div className="space-y-6">
      {notice ? (
        <Alert variant="success">
          <CheckCircle2 className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <AlertDescription>
            <div className="flex items-start justify-between gap-3">
              <span>{notice}</span>
              <button
                type="button"
                className="text-xs font-semibold text-brand-800 hover:underline"
                onClick={() => setNotice(null)}
                aria-label="Dismiss message"
              >
                Dismiss
              </button>
            </div>
          </AlertDescription>
        </Alert>
      ) : null}

      {failure ? (
        <Alert variant="error">
          <AlertDescription>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-semibold">{failure.message}</p>
                <p className="text-xs">
                  {failure.code === "RATE_LIMITED"
                    ? "Wait a little before generating again."
                    : "Nothing was saved. Review the values and try again."}
                </p>
              </div>
              <button
                type="button"
                className="text-xs font-semibold text-red-900 hover:underline"
                onClick={dismissFailure}
                aria-label="Dismiss error"
              >
                Dismiss
              </button>
            </div>
          </AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="space-y-6">
          {profile ? (
            <>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h2 className="text-lg font-semibold text-ink">Household profile</h2>
                  <p className="text-sm text-ink-muted">
                    Stored on the server under your anonymous session. Changes replace the full
                    member list.
                  </p>
                </div>
                <Badge variant="neutral">{profile.size} members</Badge>
              </div>
              <HouseholdForm
                key={profile.updated_at}
                initial={profile}
                healthConsent={session.healthConsent}
                busy={busy === "profile"}
                onSave={async (input, options) => {
                  const ok = await saveProfile(input, {
                    grantHealthConsent: options.grantHealthConsent,
                  });
                  if (ok) {
                    setNotice("Household profile saved.");
                  }
                  return ok;
                }}
              />
            </>
          ) : (
            <>
              <div>
                <h2 className="text-lg font-semibold text-ink">Create the household profile</h2>
                <p className="text-sm text-ink-muted">
                  Location is required so air quality can be requested for the right place. Only age
                  bands and coarse flags are stored — no names or diagnoses.
                </p>
              </div>
              <HouseholdForm
                initial={null}
                healthConsent={session.healthConsent}
                busy={busy === "profile"}
                onSave={async (input, options) => {
                  const ok = await saveProfile(input, {
                    grantHealthConsent: options.grantHealthConsent,
                  });
                  if (ok) {
                    setNotice("Family profile created.");
                  }
                  return ok;
                }}
              />
            </>
          )}

          {profile ? (
            <Card>
              <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="size-4 text-brand-700" aria-hidden="true" />
                    Generate recommendations
                  </CardTitle>
                  <Badge variant="neutral">
                    {preferences ? `${preferences.activity_windows.length} activities` : "Loading"}
                  </Badge>
                </div>
                <p className="text-sm text-ink-muted">
                  The deterministic rules engine decides each action from current or forecast
                  pollution. The model may write a short explanation afterwards.
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                {preferencesState.status === "error" ||
                preferencesState.status === "unavailable" ? (
                  <Alert variant="warning">
                    <AlertDescription>
                      Preferences could not be loaded: {preferencesState.message}
                    </AlertDescription>
                  </Alert>
                ) : null}

                {noActivities ? (
                  <Alert variant="warning">
                    <AlertDescription>
                      Add at least one activity in the preferences below before generating.
                    </AlertDescription>
                  </Alert>
                ) : null}

                <div className="flex flex-wrap items-center gap-3">
                  <Button
                    type="button"
                    onClick={async () => {
                      const ok = await generate();
                      if (ok) {
                        setNotice("Recommendations generated and saved to history.");
                      }
                    }}
                    disabled={busy === "generate" || noActivities || !preferences}
                  >
                    <Play className="size-4" aria-hidden="true" />
                    {busy === "generate" ? "Generating…" : "Generate recommendations"}
                  </Button>
                  {latestGeneratedAt ? (
                    <p className="text-xs text-ink-muted">
                      Latest run {formatDateTime(latestGeneratedAt)}
                    </p>
                  ) : null}
                </div>
              </CardContent>
            </Card>
          ) : null}

          {batch ? <BatchResults batch={batch} /> : null}

          {profile ? (
            <section aria-labelledby="family-history-heading" className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2
                  id="family-history-heading"
                  className="flex items-center gap-2 text-lg font-semibold text-ink"
                >
                  <History className="size-4 text-brand-700" aria-hidden="true" />
                  Saved recommendation history
                </h2>
                {history ? <Badge variant="neutral">{history.items.length} stored</Badge> : null}
              </div>

              {historyState.status === "loading" && !history ? (
                <Skeleton className="h-32 w-full" />
              ) : historyState.status === "error" || historyState.status === "unavailable" ? (
                <Alert variant="warning">
                  <AlertDescription>{historyState.message}</AlertDescription>
                </Alert>
              ) : storedItems.length === 0 ? (
                <p className="text-sm text-ink-muted">
                  {batch
                    ? "No older recommendations were stored before this run."
                    : "No recommendations stored yet. Generate a run to start the history."}
                </p>
              ) : (
                <div className="space-y-3">
                  {storedItems.map((item) => (
                    <RecommendationCard key={item.recommendation_id} recommendation={item} />
                  ))}
                  {hasMoreHistory ? (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={loadMoreHistory}
                      disabled={historyState.status === "loading"}
                    >
                      {historyState.status === "loading" ? "Loading…" : "Load more"}
                    </Button>
                  ) : null}
                </div>
              )}
            </section>
          ) : null}
        </div>

        <aside className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="size-4 text-brand-700" aria-hidden="true" />
                Profile summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {profile ? (
                <ProfileSummary profile={profile} healthConsent={session.healthConsent} />
              ) : (
                <p className="leading-relaxed text-ink-muted">
                  No family profile stored for this session yet. The form on this page creates it.
                </p>
              )}
            </CardContent>
          </Card>

          <div className="rounded-2xl border border-brand-100 bg-brand-50/70 p-4">
            <p className="flex items-center gap-2 text-sm font-semibold text-brand-900">
              <Lock className="size-4" aria-hidden="true" />
              Anonymous session
            </p>
            <p className="mt-1.5 text-xs leading-relaxed text-brand-900/80">
              A random token in this browser identifies the stored profile. The backend keeps only
              its hash. Expires {formatDateTime(session.expiresAt)}.
            </p>
            <p className="mt-1.5 text-xs leading-relaxed text-brand-900/80">
              There is no account recovery: clearing browser storage loses access to this
              session&apos;s data.
            </p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Data controls</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {profile ? (
                confirmDeleteProfile ? (
                  <div className="space-y-2">
                    <p className="text-xs leading-relaxed text-ink-muted">
                      Delete the household, members, preferences and every stored recommendation?
                      The anonymous session itself remains.
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        type="button"
                        variant="destructive"
                        size="sm"
                        disabled={busy === "delete"}
                        onClick={async () => {
                          const ok = await removeProfile();
                          setConfirmDeleteProfile(false);
                          if (ok) {
                            setNotice("Household profile and stored recommendations deleted.");
                          }
                        }}
                      >
                        <Trash2 className="size-3.5" aria-hidden="true" />
                        Delete profile
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setConfirmDeleteProfile(false)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setConfirmEndSession(false);
                      setConfirmDeleteProfile(true);
                    }}
                  >
                    Delete household profile
                  </Button>
                )
              ) : null}

              <Separator />

              {confirmEndSession ? (
                <div className="space-y-2">
                  <p className="text-xs leading-relaxed text-ink-muted">
                    Delete the session and all data stored for it? This removes the profile and
                    recommendation history permanently.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      disabled={busy === "delete"}
                      onClick={async () => {
                        const ok = await endSession();
                        setConfirmEndSession(false);
                        if (ok) {
                          setNotice("Session and all stored data deleted.");
                        }
                      }}
                    >
                      <Trash2 className="size-3.5" aria-hidden="true" />
                      Delete session
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setConfirmEndSession(false)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="text-red-700 hover:bg-red-50 hover:text-red-800"
                  onClick={() => {
                    setConfirmDeleteProfile(false);
                    setConfirmEndSession(true);
                  }}
                >
                  End session and delete all data
                </Button>
              )}
            </CardContent>
          </Card>
        </aside>
      </div>

      {profile && preferences ? (
        <section aria-labelledby="family-preferences-heading" className="space-y-3">
          <div>
            <h2 id="family-preferences-heading" className="text-lg font-semibold text-ink">
              Activity preferences
            </h2>
            <p className="text-sm text-ink-muted">
              Times, flexibility, indoor alternatives and transport preferences are stored with the
              profile and used on every generate call.
            </p>
          </div>
          <PreferencesForm
            key={preferences.updated_at}
            initial={preferences}
            busy={busy === "preferences"}
            onSave={async (input) => {
              const ok = await savePreferences(input);
              if (ok) {
                setNotice("Activity preferences saved.");
              }
              return ok;
            }}
          />
        </section>
      ) : null}
    </div>
  );
}

function ProfileSummary({
  profile,
  healthConsent,
}: {
  profile: FamilyProfile;
  healthConsent: boolean;
}) {
  return (
    <>
      <div>
        <p className="font-semibold text-ink">{profile.name}</p>
        <p className="text-xs text-ink-muted">
          {profile.city ?? "No city label"} · {profile.timezone} · updated{" "}
          {formatDateTime(profile.updated_at)}
        </p>
      </div>
      <dl className="space-y-2">
        <div>
          <dt className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
            Members
          </dt>
          <dd className="mt-1 space-y-1.5">
            {profile.members.map((member, index) => (
              <div key={member.id} className="rounded-lg border border-line px-2.5 py-2 text-xs">
                <p className="font-medium text-ink">
                  Member {index + 1} ·{" "}
                  {AGE_BAND_OPTIONS.find((band) => band.value === member.age_band)?.label ??
                    member.age_band}
                </p>
                {member.health_flags.length > 0 ? (
                  <p className="mt-0.5 text-[11px] text-ink-muted">
                    {member.health_flags
                      .map((flag) => HEALTH_FLAG_LABELS[flag] ?? flag)
                      .join(" · ")}
                  </p>
                ) : null}
              </div>
            ))}
          </dd>
        </div>
        <div className="flex flex-wrap gap-1">
          {profile.has_children ? <Badge variant="neutral">Children</Badge> : null}
          {profile.has_older_adults ? <Badge variant="neutral">Older adults</Badge> : null}
          {profile.has_health_flags ? <Badge variant="neutral">Health flags</Badge> : null}
          <Badge variant="neutral">
            {healthConsent ? "Health consent granted" : "No health consent"}
          </Badge>
        </div>
      </dl>
      <p className="text-[11px] leading-relaxed text-slate-500">
        Health flags guide general precautions with public-health attribution. They are not a
        diagnosis.
      </p>
    </>
  );
}

function BatchResults({ batch }: { batch: FamilyRecommendationBatch }) {
  const context = batch.pollution_context;
  return (
    <section aria-labelledby="family-results-heading" className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="family-results-heading" className="text-lg font-semibold text-ink">
          Latest recommendations
        </h2>
        <Badge variant="neutral">Rules {batch.rules_version}</Badge>
      </div>

      <div className="rounded-xl border border-line bg-slate-50/60 px-4 py-3 text-xs text-ink-muted">
        <span className="font-semibold text-ink">
          {context.aqi !== null
            ? `CPCB AQI ${context.aqi}${context.category ? ` · ${titleCase(context.category)}` : ""}`
            : "No CPCB AQI"}
        </span>
        {context.pm2_5 !== null ? ` · PM2.5 ${context.pm2_5} µg/m³` : ""}
        {` · ${context.provider ?? "no provider"}`}
        {` · ${context.guidance_basis_label}`}
        {context.forecast_only ? " · forecast only, not a ground measurement" : ""}
        {context.stale ? " · stale reading not treated as current" : ""}
      </div>

      <AiExplanationNotice batch={batch} />

      {batch.recommendations.length === 0 ? (
        <Alert variant="warning">
          <AlertDescription>
            The rules engine returned no recommendations for the saved activity windows.
          </AlertDescription>
        </Alert>
      ) : (
        <div className="space-y-3">
          {batch.recommendations.map((recommendation) => (
            <RecommendationCard
              key={recommendation.recommendation_id}
              recommendation={recommendation}
            />
          ))}
        </div>
      )}

      <p className="text-xs leading-relaxed text-slate-500">{batch.disclaimer}</p>
      <p className="text-[11px] text-slate-500">
        Activities evaluated:{" "}
        {batch.recommendations.map((item) => ACTIVITY_LABELS[item.activity]).join(", ") || "none"}
      </p>
    </section>
  );
}

function AiExplanationNotice({ batch }: { batch: FamilyRecommendationBatch }) {
  const explanation = batch.ai_explanation;
  if (explanation.status === "available" && explanation.text) {
    return (
      <Alert variant="info">
        <Sparkles className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
        <AlertDescription>
          <p className="leading-relaxed">{explanation.text}</p>
          <p className="mt-1 text-[11px] text-sky-900/70">
            Model explanation only · {explanation.model ?? "configured model"}. Actions above are
            produced by deterministic rules.
          </p>
        </AlertDescription>
      </Alert>
    );
  }
  if (explanation.status === "rejected") {
    return (
      <Alert variant="warning">
        <AlertDescription>
          The model explanation was rejected by grounding checks
          {explanation.reason ? ` (${explanation.reason})` : ""}. The deterministic recommendations
          above are unaffected.
        </AlertDescription>
      </Alert>
    );
  }
  return (
    <Alert variant="neutral">
      <AlertDescription>
        AI explanation unavailable{explanation.reason ? ` (${explanation.reason})` : ""}. The
        deterministic recommendations above are complete without it.
      </AlertDescription>
    </Alert>
  );
}
