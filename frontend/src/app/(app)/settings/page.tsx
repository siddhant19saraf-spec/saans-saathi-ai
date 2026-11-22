import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/page-header";
import { SettingsView } from "@/components/settings/settings-view";

export const metadata: Metadata = {
  title: "Settings",
  description:
    "Notification preferences, data-source details and local data controls. Preferences are stored in this browser; no delivery channel is connected.",
};

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Workspace"
        title="Settings"
        description="Review which sources the product would use, manage notification preferences and clear anything stored on this device."
      />
      <SettingsView />
    </div>
  );
}
