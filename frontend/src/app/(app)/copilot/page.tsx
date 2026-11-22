import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/page-header";
import { CopilotView } from "@/components/copilot/copilot-view";

export const metadata: Metadata = {
  title: "Copilot",
  description:
    "Ask grounded questions about air quality and household precautions. Answers come from the Copilot service with citations; no response is simulated.",
};

export default function CopilotPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Assistant"
        title="SAANS AI Copilot"
        description="A grounded assistant for timing, indoor steps and household precautions. Every answer must cite its facts — and when the service is unavailable, the page says so instead of improvising."
      />
      <CopilotView />
    </div>
  );
}
