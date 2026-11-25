"use client";

import Link from "next/link";
import { ArrowRight, CalendarClock, CloudOff, MapPin, RefreshCw, Wind } from "lucide-react";
import { SeverityBadge } from "@/components/air-quality/severity-badge";
import { StatusBadge } from "@/components/ui/status-badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/feedback";
import type { ResourceState } from "@/features/api/resource";
import type { AirCurrent } from "@/features/air-quality/schemas";
import { severityMeta } from "@/features/air-quality/severity";
import { formatCoordinates, type SavedLocation } from "@/features/locations/schema";
import { formatValue } from "@/lib/format";
import { useMounted } from "@/lib/use-mounted";

function sourceLabel(data: AirCurrent): string | null {
  switch (data.provenance.source_type) {
    case "ground_observation":
      return "Ground-station observation";
    case "historical_observation":
      return "Historical observation";
    case "model_forecast":
      return "Model-based forecast";
    default:
      return null;
  }
}

function greetingFor(hour: number): string {
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export function DashboardHero({
  location,
  state,
  retry,
}: {
  location: SavedLocation;
  state: ResourceState<AirCurrent>;
  retry: () => void;
}) {
  const mounted = useMounted();
  const now = mounted ? new Date() : null;
  const greeting = now ? greetingFor(now.getHours()) : "Welcome";
  const today = now
    ? new Intl.DateTimeFormat("en-IN", {
        weekday: "long",
        day: "numeric",
        month: "long",
      }).format(now)
    : null;

  const data = state.status === "success" ? state.data : null;
  const aqi = data?.cpcb_aqi ?? null;
  const meta = aqi ? severityMeta[aqi.category] : null;
  const provenance = data?.provenance ?? null;
  const source = data ? sourceLabel(data) : null;

  return (
    <section
      aria-labelledby="welcome-heading"
      className="surface-hero overflow-hidden rounded-2xl border border-line shadow-card"
    >
      <div className="grid gap-6 p-5 sm:p-6 lg:grid-cols-[minmax(0,1.45fr)_minmax(18rem,1fr)] lg:items-center lg:gap-8 lg:p-7">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-[11px] font-semibold tracking-[0.16em] text-brand-700 uppercase">
            <span aria-hidden="true" className="size-1.5 rounded-full bg-accent-500" />
            Your environmental briefing
          </p>
          <h2
            id="welcome-heading"
            className="mt-2.5 text-2xl leading-tight font-semibold tracking-[-0.02em] text-ink sm:text-[1.75rem]"
          >
            {greeting}. Here is the air for{" "}
            <span className="text-brand-800">{location.label}</span>.
          </h2>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-ink-muted">
            A single view of current conditions, your household plan and the actions worth taking
            today. Unavailable data is labelled, never estimated.
          </p>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <StatusBadge tone="neutral" icon={false}>
              <MapPin className="size-3.5" aria-hidden="true" />
              {formatCoordinates(location.lat, location.lon)}
            </StatusBadge>
            {today ? (
              <StatusBadge tone="neutral" icon={false}>
                {today}
              </StatusBadge>
            ) : null}
            {source ? <StatusBadge tone="info">{source}</StatusBadge> : null}
            {provenance ? (
              <StatusBadge tone={provenance.stale ? "stale" : "positive"}>
                {provenance.stale
                  ? `Stale · ${formatValue(provenance.age_minutes)} min old`
                  : `Fresh · ${formatValue(provenance.age_minutes)} min old`}
              </StatusBadge>
            ) : null}
          </div>

          <div className="mt-5 flex flex-wrap gap-2">
            <Button asChild size="sm">
              <Link href="/air-quality">
                <Wind className="size-4" aria-hidden="true" />
                Air intelligence
                <ArrowRight className="size-3.5" aria-hidden="true" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href="/smart-routine">
                <CalendarClock className="size-4" aria-hidden="true" />
                Plan my day
              </Link>
            </Button>
          </div>
        </div>

        <div className="rounded-2xl border border-line bg-white/85 p-4 shadow-card sm:p-5">
          {state.status === "loading" || state.status === "idle" ? (
            <div aria-busy="true" aria-live="polite" className="space-y-3">
              <span className="sr-only">Loading current air quality</span>
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-12 w-24" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          ) : null}

          {state.status === "unavailable" || state.status === "error" ? (
            <div>
              <div className="flex items-center gap-2 text-ink-muted">
                <CloudOff className="size-4 shrink-0" aria-hidden="true" />
                <p className="text-xs font-semibold tracking-wide uppercase">
                  Current air quality unavailable
                </p>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-ink-muted">{state.message}</p>
              <Button type="button" variant="outline" size="sm" className="mt-3" onClick={retry}>
                <RefreshCw className="size-3.5" aria-hidden="true" />
                Retry
              </Button>
            </div>
          ) : null}

          {data ? (
            <>
              <p className="text-xs font-semibold tracking-wide text-ink-muted uppercase">
                CPCB Air Quality Index
              </p>
              {aqi ? (
                <>
                  <div className="mt-1 flex flex-wrap items-end gap-x-3 gap-y-1">
                    <p className="metric-value text-4xl leading-none font-semibold text-ink">
                      {formatValue(aqi.value)}
                    </p>
                    <SeverityBadge category={aqi.category} showRange />
                  </div>
                  {meta ? (
                    <p className="mt-2 text-sm leading-relaxed text-ink-muted">{meta.summary}</p>
                  ) : null}
                  <dl className="mt-3 grid grid-cols-2 gap-2 border-t border-line pt-3 text-xs">
                    <div>
                      <dt className="text-ink-subtle">Dominant</dt>
                      <dd className="mt-0.5 font-medium text-ink">{aqi.dominant_pollutant}</dd>
                    </div>
                    <div>
                      <dt className="text-ink-subtle">Coverage</dt>
                      <dd className="mt-0.5 font-medium text-ink">
                        {aqi.partial ? "Partial" : "Complete"}
                      </dd>
                    </div>
                  </dl>
                  {aqi.partial ? (
                    <p className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1.5 text-[11px] leading-relaxed text-amber-950">
                      One or more pollutants are missing; the category is partial.
                    </p>
                  ) : null}
                </>
              ) : (
                <>
                  <p className="mt-2 text-lg font-semibold text-ink">No CPCB index this hour</p>
                  <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">
                    {data.aqi_unavailable_reason ??
                      "Required pollutants were not reported, so no index is shown. Raw values remain available below."}
                  </p>
                </>
              )}
            </>
          ) : null}
        </div>
      </div>
    </section>
  );
}
