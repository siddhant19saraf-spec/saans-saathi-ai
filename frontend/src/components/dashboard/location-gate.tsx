import { CloudOff, MapPin, Plus } from "lucide-react";
import Link from "next/link";

import { AddLocationButton } from "@/components/navigation/add-location-dialog";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";

export function LocationGate() {
  return (
    <div className="space-y-4">
      <EmptyState
        icon={MapPin}
        title="Choose a location to begin"
        description={
          <div className="space-y-2">
            <p>
              Add coordinates, use your device location from the selector above, or pick a point on
              the OpenStreetMap view.
            </p>
            <p className="text-xs text-slate-500">
              No readings are generated locally. Until the air-quality service is connected, every
              data surface reports a labelled unavailable state.
            </p>
          </div>
        }
        action={
          <>
            <AddLocationButton label="Add coordinates" />
            <Button asChild variant="outline">
              <Link href="/map">
                <Plus className="size-4" aria-hidden="true" />
                Pick on the map
              </Link>
            </Button>
          </>
        }
      />
      <div className="flex items-start gap-2 rounded-xl border border-line bg-white px-4 py-3 text-xs leading-relaxed text-ink-muted">
        <CloudOff className="mt-0.5 size-4 shrink-0 text-slate-400" aria-hidden="true" />
        <p>
          Locations are stored in this browser only. Coordinates are rounded before they are sent to
          the backend.
        </p>
      </div>
    </div>
  );
}
