import type { Metadata } from "next";
import Link from "next/link";

import { AirQualityView } from "@/components/air-quality/air-quality-view";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Air intelligence",
  description:
    "CPCB 2014 AQI with pollutant concentrations, source type, station details and freshness. Model-based forecasts are labelled separately from ground-station observations.",
};

export default function AirQualityPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Air intelligence"
        title="Air quality in detail"
        description="CPCB index and pollutant concentrations with provider, observation time and freshness. Forecast and history render only when the provider responds."
        actions={
          <Button asChild variant="outline">
            <Link href="/dashboard">Back to dashboard</Link>
          </Button>
        }
      />
      <AirQualityView />
    </div>
  );
}
