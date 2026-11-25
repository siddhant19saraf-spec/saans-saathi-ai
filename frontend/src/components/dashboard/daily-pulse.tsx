"use client";

import { CalendarClock, House, Leaf, Users } from "lucide-react";

import { MetricCard } from "@/components/ui/metric-card";
import { SectionHeader } from "@/components/ui/section-header";
import { useFamilyOverview } from "@/features/family/use-family";
import { INDOOR_CHECKLIST } from "@/features/indoor/schema";
import { useIndoorChecklist } from "@/features/indoor/use-indoor";
import { useImpactActivities } from "@/features/impact/use-impact";
import { sortByStart } from "@/features/routine/schema";
import { useRoutineActivities } from "@/features/routine/use-routine";

export function DailyPulse() {
  const { profile, state: familyState } = useFamilyOverview();
  const { activities: routine, hydrated: routineHydrated } = useRoutineActivities();
  const { completed, hydrated: indoorHydrated } = useIndoorChecklist();
  const { activities: impact, hydrated: impactHydrated } = useImpactActivities();

  const orderedRoutine = sortByStart(routine);
  const next = orderedRoutine[0] ?? null;
  const indoorTotal = INDOOR_CHECKLIST.length;
  const indoorPercent = indoorTotal > 0 ? Math.round((completed / indoorTotal) * 100) : 0;

  return (
    <section aria-labelledby="daily-pulse-heading" className="space-y-3">
      <SectionHeader
        id="daily-pulse-heading"
        title="Your day at a glance"
        description="Household readiness, routine, indoor actions and logged impact — from data stored for this workspace."
      />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Family readiness"
          icon={Users}
          value={profile ? profile.size : null}
          unit={profile && profile.size === 1 ? "member" : "members"}
          emptyLabel={
            familyState.status === "loading" ? "Loading profile…" : "No profile yet"
          }
          hint={
            profile
              ? profile.has_health_flags
                ? "Health flags noted · general precautions only"
                : "No health flags recorded"
              : "Create an anonymous household profile"
          }
          href="/family"
          actionLabel="Family intelligence"
        />
        <MetricCard
          label="Routine"
          icon={CalendarClock}
          value={routineHydrated && routine.length > 0 ? routine.length : null}
          unit={routine.length === 1 ? "activity" : "activities"}
          emptyLabel={routineHydrated ? "No activities yet" : "Loading routine…"}
          hint={
            next
              ? `First up: ${next.start} · ${next.title}`
              : "Add a walk, commute or indoor routine"
          }
          href="/smart-routine"
          actionLabel="Open SmartRoutine"
        />
        <MetricCard
          label="Indoor protection"
          icon={House}
          value={indoorHydrated && completed > 0 ? `${completed}/${indoorTotal}` : null}
          unit="checks"
          emptyLabel={indoorHydrated ? "Checklist not started" : "Loading checklist…"}
          hint={
            indoorHydrated
              ? completed === indoorTotal && completed > 0
                ? "Every checklist item is marked complete"
                : `${indoorPercent}% of the household checklist complete`
              : "Progress is stored in this browser"
          }
          href="/indoor-shield"
          actionLabel="Open IndoorShield"
          tone={completed === indoorTotal && completed > 0 ? "positive" : "default"}
        />
        <MetricCard
          label="Impact log"
          icon={Leaf}
          value={impactHydrated && impact.length > 0 ? impact.length : null}
          unit={impact.length === 1 ? "entry" : "entries"}
          emptyLabel={impactHydrated ? "Nothing logged yet" : "Loading log…"}
          hint={
            impact.length > 0
              ? "Activity quantities only — no emissions are calculated here"
              : "Record a low-carbon trip or action"
          }
          href="/impact"
          actionLabel="Open Impact"
        />
      </div>
    </section>
  );
}
