"use client";

import Link from "next/link";
import { Activity, Bell, Users } from "lucide-react";

import { SeverityBadge } from "@/components/air-quality/severity-badge";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/feedback";
import type { ResourceState } from "@/features/api/resource";
import type { AirCurrent } from "@/features/air-quality/schemas";
import { severityMeta } from "@/features/air-quality/severity";
import { AGE_BAND_OPTIONS, HEALTH_FLAG_LABELS } from "@/features/family/schema";
import { useFamilyOverview } from "@/features/family/use-family";
import { useNotificationPreferences } from "@/features/settings/use-settings";

const preferenceLabels = [
  { key: "airQualityAlerts", label: "Air quality alerts" },
  { key: "routineReminders", label: "Routine reminders" },
  { key: "weeklyImpact", label: "Weekly impact summary" },
] as const;

export function InsightsPanel({ airState }: { airState: ResourceState<AirCurrent> }) {
  const { profile: household, state: householdState, session } = useFamilyOverview();
  const { preferences } = useNotificationPreferences();

  const data = airState.status === "success" ? airState.data : null;
  const aqi = data?.cpcb_aqi ?? null;
  const meta = aqi ? severityMeta[aqi.category] : null;
  const sensitive = household?.has_health_flags;

  return (
    <section aria-labelledby="insights-heading" className="space-y-4">
      <div>
        <h2 id="insights-heading" className="text-lg font-semibold text-ink">
          Personalised insights
        </h2>
        <p className="mt-0.5 text-sm text-ink-muted">
          Context for your household. No risk score is invented when the intelligence service is
          unavailable.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="size-4 text-brand-700" aria-hidden="true" />
              Household
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {household ? (
              <>
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold text-ink">{household.name}</p>
                  <Badge variant="neutral">
                    {household.members.length} member
                    {household.members.length === 1 ? "" : "s"}
                  </Badge>
                </div>
                <ul className="space-y-1.5">
                  {household.members.map((member, index) => (
                    <li key={member.id} className="text-xs text-ink-muted">
                      <span className="font-medium text-ink">Member {index + 1}</span>
                      {" · "}
                      {AGE_BAND_OPTIONS.find((band) => band.value === member.age_band)?.label ??
                        member.age_band}
                      {member.health_flags.length > 0 ? (
                        <span className="block text-slate-500">
                          {member.health_flags
                            .map((flag) => HEALTH_FLAG_LABELS[flag] ?? flag)
                            .join(" · ")}
                        </span>
                      ) : null}
                    </li>
                  ))}
                </ul>
                <Separator />
                {meta ? (
                  <div className="space-y-2">
                    <p className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
                      General CPCB context
                    </p>
                    <p className="text-sm leading-relaxed text-ink-muted">
                      {meta.label} conditions: {meta.summary}
                    </p>
                    {sensitive ? (
                      <p className="text-xs leading-relaxed text-slate-500">
                        Your profile includes health flags. Treat this as general category context,
                        not a personal medical assessment.
                      </p>
                    ) : null}
                  </div>
                ) : (
                  <p className="text-xs leading-relaxed text-ink-muted">
                    Household-specific recommendations need current air-quality data. The risk
                    service is not connected in this build.
                  </p>
                )}
                <Link
                  href="/family"
                  className="inline-flex text-xs font-semibold text-brand-700 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
                >
                  Edit household profile
                </Link>
              </>
            ) : (
              <>
                <p className="leading-relaxed text-ink-muted">
                  Add age bands and optional general health flags so guidance can account for who is
                  breathing the air.
                </p>
                <p className="text-xs text-slate-500">
                  {!session
                    ? "No family session yet."
                    : householdState.status === "loading"
                      ? "Loading the family profile…"
                      : householdState.status === "unavailable" || householdState.status === "error"
                        ? "The family profile could not be loaded from this session."
                        : "Stored under an anonymous session."}
                </p>
                <Link
                  href="/family"
                  className="inline-flex text-xs font-semibold text-brand-700 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
                >
                  Create a household profile
                </Link>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="size-4 text-brand-700" aria-hidden="true" />
              Activity precautions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {meta ? (
              <>
                <SeverityBadge category={aqi?.category ?? null} showRange />
                <p className="leading-relaxed text-ink-muted">{meta.summary}</p>
                <p className="text-xs leading-relaxed text-slate-500">
                  General category guidance. Timing for specific activities comes from the
                  SmartRoutine service, which is not connected in this build.
                </p>
              </>
            ) : (
              <p className="leading-relaxed text-ink-muted">
                Activity precautions require current air-quality data. The intelligence service is
                not connected, so no precaution is generated.
              </p>
            )}
            <Link
              href="/smart-routine"
              className="inline-flex text-xs font-semibold text-brand-700 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
            >
              Open SmartRoutine
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="size-4 text-brand-700" aria-hidden="true" />
              Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <ul className="space-y-1.5">
              {preferenceLabels.map(({ key, label }) => (
                <li key={key} className="flex items-center justify-between gap-2 text-xs">
                  <span className="text-ink-muted">{label}</span>
                  <Badge variant={preferences[key] ? "default" : "outline"}>
                    {preferences[key] ? "On (local)" : "Off"}
                  </Badge>
                </li>
              ))}
            </ul>
            <p className="text-xs leading-relaxed text-slate-500">
              No alert delivery channel is connected, so no notifications are generated or assumed.
            </p>
            <Link
              href="/settings#notifications"
              className="inline-flex text-xs font-semibold text-brand-700 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
            >
              Manage preferences
            </Link>
          </CardContent>
        </Card>
      </div>

      <p className="rounded-xl border border-line bg-white px-4 py-3 text-xs leading-relaxed text-ink-muted">
        Household risk scoring, exposure dose and alert generation are backend intelligence
        services. This build shows general CPCB category context and clearly marks what is not
        connected.
      </p>
    </section>
  );
}
