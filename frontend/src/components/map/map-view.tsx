"use client";

import dynamic from "next/dynamic";
import { Check, Info, MapPin, MousePointerClick } from "lucide-react";
import { useState } from "react";

import { AddLocationDialog } from "@/components/navigation/add-location-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/feedback";
import { useLocations } from "@/features/locations/location-context";
import { formatCoordinates } from "@/features/locations/schema";
import { cn } from "@/lib/utils";

const MapCanvas = dynamic(() => import("./map-canvas").then((module) => module.MapCanvas), {
  ssr: false,
  loading: () => (
    <div
      aria-busy="true"
      aria-live="polite"
      className="flex h-[26rem] items-center justify-center bg-slate-100 sm:h-[32rem]"
    >
      <span className="sr-only">Loading the map</span>
      <Skeleton className="h-3/4 w-3/4" />
    </div>
  ),
});

type PickedPoint = { lat: number; lon: number };

export function MapView() {
  const { locations, activeLocation, setActiveLocation, hydrated } = useLocations();
  const [picked, setPicked] = useState<PickedPoint | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  if (!hydrated) {
    return (
      <div aria-busy="true" aria-live="polite" className="space-y-4">
        <span className="sr-only">Loading saved locations</span>
        <Skeleton className="h-[26rem] w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-[1.65fr_1fr]">
        <Card className="overflow-hidden">
          <CardHeader className="border-b border-line pb-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle className="flex items-center gap-2">
                <MapPin className="size-4 text-brand-700" aria-hidden="true" />
                OpenStreetMap
              </CardTitle>
              <Badge variant="outline">Tiles © OpenStreetMap contributors</Badge>
            </div>
            <p className="flex items-center gap-1.5 text-xs text-ink-muted">
              <MousePointerClick className="size-3.5" aria-hidden="true" />
              Click the map to choose a coordinate, then confirm the point.
            </p>
          </CardHeader>
          <CardContent className="p-0">
            <div
              className="relative overflow-hidden border-b border-line"
              role="region"
              aria-label="Interactive OpenStreetMap with saved locations"
            >
              <MapCanvas
                locations={locations}
                activeId={activeLocation?.id ?? null}
                onPick={(lat, lon) => {
                  setPicked({ lat, lon });
                  setDialogOpen(true);
                }}
                onActivate={setActiveLocation}
              />
            </div>
            <p className="px-4 py-3 text-xs leading-relaxed text-ink-muted">
              Use the map controls or your keyboard to move and zoom. The saved locations list
              beside the map is an equivalent way to choose a place. No monitoring stations are
              plotted — a map point is a coordinate, not a measurement.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Saved locations</CardTitle>
            <p className="text-sm text-ink-muted">Stored in this browser. Up to eight places.</p>
          </CardHeader>
          <CardContent className="space-y-3">
            {locations.length === 0 ? (
              <p className="rounded-xl border border-dashed border-line bg-slate-50 px-4 py-6 text-sm leading-relaxed text-ink-muted">
                No saved locations yet. Click the map and confirm a point, or add coordinates
                directly.
              </p>
            ) : (
              <ul className="flex flex-col gap-1.5">
                {locations.map((location) => {
                  const active = location.id === activeLocation?.id;
                  return (
                    <li
                      key={location.id}
                      className={cn(
                        "rounded-xl border px-3 py-2.5",
                        active ? "border-brand-200 bg-brand-50" : "border-line",
                      )}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-ink">{location.label}</p>
                          <p className="text-xs text-ink-muted">
                            {formatCoordinates(location.lat, location.lon)}
                          </p>
                        </div>
                        {active ? (
                          <Badge>
                            <Check className="size-3" aria-hidden="true" />
                            Active
                          </Badge>
                        ) : (
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => setActiveLocation(location.id)}
                          >
                            Set active
                          </Button>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}

            <Button
              type="button"
              className="w-full"
              onClick={() => {
                setPicked(null);
                setDialogOpen(true);
              }}
            >
              Add coordinates
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="flex items-start gap-3 rounded-xl border border-line bg-white px-4 py-3 text-sm leading-relaxed text-ink-muted">
        <Info className="mt-0.5 size-4 shrink-0 text-brand-700" aria-hidden="true" />
        <div>
          <p className="font-medium text-ink">About this map</p>
          <p className="mt-1 text-xs">
            Tiles are served by OpenStreetMap with attribution. Coordinates are rounded to two
            decimal places before they are sent to the backend. There is no station layer because
            this build has no connected monitoring data; fabricated stations are never displayed.
          </p>
        </div>
      </div>

      <AddLocationDialog
        open={dialogOpen}
        onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) {
            setPicked(null);
          }
        }}
        initial={picked}
        source="map"
      />
    </div>
  );
}
