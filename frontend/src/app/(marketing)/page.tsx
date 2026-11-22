import type { Metadata } from "next";

import { AccessibilitySection } from "@/components/marketing/accessibility-section";
import { CapabilityStrip } from "@/components/marketing/capability-strip";
import { CopilotSection } from "@/components/marketing/copilot-section";
import { CtaSection } from "@/components/marketing/cta-section";
import { FaqSection } from "@/components/marketing/faq-section";
import { Hero } from "@/components/marketing/hero";
import { HowItWorks } from "@/components/marketing/how-it-works";
import { ModulesSection } from "@/components/marketing/modules-section";
import { ProblemSection } from "@/components/marketing/problem-section";
import { StandardsSection } from "@/components/marketing/standards-section";

export const metadata: Metadata = {
  // Route-group pages share the root segment, so the template does not apply.
  title: {
    absolute: "SAANS SAATHI AI — air intelligence for everyday breathing",
  },
  description:
    "A personal air-quality workspace for Indian cities: CPCB AQI context, household routines, indoor guidance, sustainability tracking and a grounded AI copilot.",
};

export default function LandingPage() {
  return (
    <>
      <Hero />
      <CapabilityStrip />
      <ProblemSection />
      <ModulesSection />
      <HowItWorks />
      <StandardsSection />
      <AccessibilitySection />
      <CopilotSection />
      <FaqSection />
      <CtaSection />
    </>
  );
}
