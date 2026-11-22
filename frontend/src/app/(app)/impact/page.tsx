import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/page-header";
import { ImpactView } from "@/components/impact/impact-view";

export const metadata: Metadata = {
  title: "Impact",
  description:
    "Keep a personal log of low-carbon activities. Emission totals are shown only from the server-side factor registry with full provenance.",
};

export default function ImpactPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Decisions"
        title="Impact"
        description="A private log of actions you take, plus the emission factors the server publishes. No savings are invented when the accounting service is absent."
      />
      <ImpactView />
    </div>
  );
}
