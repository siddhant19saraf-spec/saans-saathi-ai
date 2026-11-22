"use client";

import { useAirCurrent } from "@/features/air-quality/api";
import { useLocations } from "@/features/locations/location-context";
import { Skeleton } from "@/components/ui/feedback";

import { AnalyticsSection } from "./analytics-section";
import { CurrentAirSection } from "./current-air-section";
import { InsightsPanel } from "./insights-panel";
import { LocationGate } from "./location-gate";
import { SmartActions } from "./smart-actions";

export function DashboardView() {
  const { activeLocation, hydrated } = useLocations();
  const current = useAirCurrent(activeLocation);

  if (!hydrated) {
    return (
      <div aria-busy="true" aria-live="polite" className="space-y-4">
        <span className="sr-only">Loading your workspace</span>
        <Skeleton className="h-24 w-full" />
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-72 w-full" />
          <Skeleton className="h-72 w-full" />
        </div>
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (!activeLocation) {
    return <LocationGate />;
  }

  return (
    <div className="space-y-10">
      <CurrentAirSection location={activeLocation} state={current.state} retry={current.retry} />
      <AnalyticsSection location={activeLocation} />
      <InsightsPanel airState={current.state} />
      <SmartActions />
    </div>
  );
}
