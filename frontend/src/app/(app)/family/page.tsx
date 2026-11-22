import type { Metadata } from "next";

import { FamilyView } from "@/components/family/family-view";
import { PageHeader } from "@/components/shared/page-header";

export const metadata: Metadata = {
  title: "Family intelligence",
  description:
    "Store a household profile with age bands and optional general health flags, configure activity windows, and generate deterministic air-quality recommendations from validated pollution data.",
};

export default function FamilyPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Protection"
        title="Family intelligence"
        description="Household profiles and activity preferences stored under an anonymous session. Every action comes from deterministic rules using validated pollution data; the AI model only explains it. General guidance — never a diagnosis."
      />
      <FamilyView />
    </div>
  );
}
