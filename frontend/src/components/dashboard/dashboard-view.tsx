"use client";

import { useAirCurrent } from "@/features/air-quality/api";
import { useLocations } from "@/features/locations/location-context";
import { Skeleton } from "@/components/ui/feedback";

import { AnalyticsSection } from "./analytics-section";
import { CurrentAirSection } from "./current-air-section";
import { DailyPulse } from "./daily-pulse";
import { DashboardHero } from "./dashboard-hero";
import { InsightsPanel } from "./insights-panel";
import { LocationGate } from "./location-gate";
import { QuickActions } from "./quick-actions";
import { RecentActivity } from "./recent-activity";

export function DashboardView() {
  const { activeLocation, hydrated } = useLocations();
  const current = useAirCurrent(activeLocation);

  if (!hydrated) {
    return (
      <div aria-busy="true" aria-live="polite" className="space-y-4">
        <span className="sr-only">Loading your workspace</span>
        <Skeleton className="h-56 w-full rounded-2xl" />
        <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
          <Skeleton className="h-20 w-full rounded-2xl" />
          <Skeleton className="h-20 w-full rounded-2xl" />
          <Skeleton className="h-20 w-full rounded-2xl" />
          <Skeleton className="h-20 w-full rounded-2xl" />
        </div>
        <Skeleton className="h-80 w-full rounded-2xl" />
      </div>
    );
  }

  if (!activeLocation) {
    return <LocationGate />;
  }

  return (
    <div className="space-y-9">
      <DashboardHero location={activeLocation} state={current.state} retry={current.retry} />
      <QuickActions />
      <CurrentAirSection location={activeLocation} state={current.state} retry={current.retry} />
      <DailyPulse />
      <RecentActivity />
      <AnalyticsSection location={activeLocation} />
      <InsightsPanel airState={current.state} />
    </div>
  );
}
