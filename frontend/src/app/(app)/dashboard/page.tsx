import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { DashboardView } from "@/components/dashboard/dashboard-view";
import { AddLocationButton } from "@/components/navigation/add-location-dialog";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Dashboard",
  description:
    "Current CPCB air quality, pollutant concentrations, provenance, forecast, history and household context for the selected location.",
};

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Overview"
        title="Today’s air intelligence"
        description="Current conditions, data provenance and household context for the selected location. Every unavailable surface says so."
        actions={
          <>
            <AddLocationButton />
            <Button asChild variant="outline">
              <Link href="/air-quality">
                Detailed analysis
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
          </>
        }
      />
      <DashboardView />
    </div>
  );
}
