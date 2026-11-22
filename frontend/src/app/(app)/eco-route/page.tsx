import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/page-header";
import { EcoRouteView } from "@/components/eco-route/eco-route-view";

export const metadata: Metadata = {
  title: "EcoRoute",
  description:
    "Compare travel modes for carbon and exposure using the route comparison service. No estimate is substituted when the service is unavailable.",
};

export default function EcoRoutePage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Decisions"
        title="EcoRoute"
        description="Compare travel modes for carbon and, when real air-quality data is available, modelled exposure. Preferences stay on this device; comparison results come from the server."
      />
      <EcoRouteView />
    </div>
  );
}
