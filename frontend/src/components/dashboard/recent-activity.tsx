"use client";

import Link from "next/link";
import { Activity, ArrowRight, CalendarClock, Leaf } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";
import { labelFor, unitFor } from "@/features/impact/schema";
import { useImpactActivities } from "@/features/impact/use-impact";
import { INTENSITIES, VENUES, sortByStart } from "@/features/routine/schema";
import { useRoutineActivities } from "@/features/routine/use-routine";
import { formatDay, formatValue } from "@/lib/format";

export function RecentActivity() {
  const { activities: impact, hydrated: impactHydrated } = useImpactActivities();
  const { activities: routine, hydrated: routineHydrated } = useRoutineActivities();

  const recentImpact = [...impact].slice(0, 3);
  const recentRoutine = sortByStart(routine).slice(0, 3);
  const empty = recentImpact.length === 0 && recentRoutine.length === 0;

  return (
    <section aria-labelledby="recent-activity-heading" className="space-y-3">
      <SectionHeader
        id="recent-activity-heading"
        title="Recent activity"
        description="Your latest plan and log entries. Nothing is sent anywhere."
        actions={
          <Link
            href="/impact"
            className="inline-flex items-center gap-1 text-xs font-semibold text-brand-700 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
          >
            View impact log
            <ArrowRight className="size-3.5" aria-hidden="true" />
          </Link>
        }
      />

      {!impactHydrated || !routineHydrated ? (
        <Card>
          <CardContent className="py-6 text-sm text-ink-muted">Loading local activity…</CardContent>
        </Card>
      ) : empty ? (
        <EmptyState
          icon={Activity}
          title="No activity yet"
          description="Add a routine activity or log a low-carbon action. Entries stay in this browser and are never presented as measured emissions."
          action={
            <>
              <Link
                href="/smart-routine"
                className="text-sm font-semibold text-brand-800 underline-offset-2 hover:underline"
              >
                Plan a routine
              </Link>
              <Link
                href="/impact"
                className="text-sm font-semibold text-brand-800 underline-offset-2 hover:underline"
              >
                Log an action
              </Link>
            </>
          }
        />
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          <Card>
            <CardHeader className="flex-row items-center justify-between gap-2 pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <CalendarClock className="size-4 text-brand-700" aria-hidden="true" />
                Today&apos;s routine
              </CardTitle>
              <Link
                href="/smart-routine"
                className="text-[11px] font-semibold text-brand-700 hover:underline"
              >
                Open
              </Link>
            </CardHeader>
            <CardContent>
              {recentRoutine.length === 0 ? (
                <p className="text-sm text-ink-muted">No routine activities saved yet.</p>
              ) : (
                <ul className="divide-y divide-line">
                  {recentRoutine.map((activity) => (
                    <li
                      key={activity.id}
                      className="flex items-start justify-between gap-3 py-2.5 first:pt-0 last:pb-0"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-ink">{activity.title}</p>
                        <p className="mt-0.5 text-xs text-ink-muted">
                          {VENUES.find((venue) => venue.value === activity.venue)?.label ??
                            activity.venue}
                          {" · "}
                          {INTENSITIES.find((intensity) => intensity.value === activity.intensity)
                            ?.label ?? activity.intensity}
                          {" · "}
                          {activity.durationMin} min
                        </p>
                      </div>
                      <span className="metric-value shrink-0 text-sm font-semibold text-brand-800">
                        {activity.start}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex-row items-center justify-between gap-2 pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Leaf className="size-4 text-brand-700" aria-hidden="true" />
                Latest impact entries
              </CardTitle>
              <Link href="/impact" className="text-[11px] font-semibold text-brand-700 hover:underline">
                Open
              </Link>
            </CardHeader>
            <CardContent>
              {recentImpact.length === 0 ? (
                <p className="text-sm text-ink-muted">Nothing logged yet.</p>
              ) : (
                <ul className="divide-y divide-line">
                  {recentImpact.map((activity) => (
                    <li
                      key={activity.id}
                      className="flex items-start justify-between gap-3 py-2.5 first:pt-0 last:pb-0"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-ink">
                          {labelFor(activity.type)}
                        </p>
                        <p className="mt-0.5 text-xs text-ink-muted">
                          {formatValue(activity.quantity, 2)} {unitFor(activity.type)}
                        </p>
                      </div>
                      <span className="shrink-0 text-xs text-ink-subtle">
                        {formatDay(activity.occurredOn)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </section>
  );
}
