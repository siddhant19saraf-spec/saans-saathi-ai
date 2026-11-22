import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/page-header";
import { RoutineView } from "@/components/smart-routine/routine-view";

export const metadata: Metadata = {
  title: "SmartRoutine",
  description:
    "Plan daily activities by time, venue and intensity. Exposure-aware timing requires the SmartRoutine service and current air-quality data.",
};

export default function SmartRoutinePage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Protection"
        title="SmartRoutine"
        description="Build a day plan that is saved on this device. Timing guidance appears only when the air-quality and routine services are connected — the planner never invents an exposure ranking."
      />
      <RoutineView />
    </div>
  );
}
