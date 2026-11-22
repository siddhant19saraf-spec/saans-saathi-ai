import type { Metadata } from "next";
import Link from "next/link";

import { MapView } from "@/components/map/map-view";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Pollution map",
  description:
    "Choose a location on an OpenStreetMap view. Saved places are coordinates, not monitoring stations.",
};

export default function MapPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Pollution map"
        title="Choose a place on the map"
        description="OpenStreetMap tiles with your saved places. A map point is a coordinate, not a measurement; no monitoring stations are drawn without a connected provider."
        actions={
          <Button asChild variant="outline">
            <Link href="/air-quality">Air intelligence</Link>
          </Button>
        }
      />
      <MapView />
    </div>
  );
}
