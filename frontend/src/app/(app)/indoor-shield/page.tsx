import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/page-header";
import { IndoorView } from "@/components/indoor-shield/indoor-view";

export const metadata: Metadata = {
  title: "IndoorShield",
  description:
    "A practical indoor air checklist covering ventilation, dust, kitchen sources and filtration. Local to this device; not an indoor measurement.",
};

export default function IndoorShieldPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Protection"
        title="IndoorShield"
        description="General household measures that reduce indoor particle sources. Your checklist progress is stored on this device — no indoor sensor data is claimed."
      />
      <IndoorView />
    </div>
  );
}
