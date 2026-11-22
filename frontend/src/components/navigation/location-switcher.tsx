"use client";

import { Check, ChevronDown, LocateFixed, MapPin, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/feedback";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useLocations } from "@/features/locations/location-context";
import { formatCoordinates } from "@/features/locations/schema";
import { cn } from "@/lib/utils";

import { AddLocationDialog } from "./add-location-dialog";

type GeoStatus = { state: "idle" | "locating" } | { state: "error"; message: string };

export function LocationSwitcher() {
  const { locations, activeLocation, setActiveLocation, removeLocation, addLocation } =
    useLocations();
  const [open, setOpen] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [geo, setGeo] = useState<GeoStatus>({ state: "idle" });

  const triggerLabel = activeLocation?.label ?? "Set location";

  function useDeviceLocation() {
    if (typeof navigator === "undefined" || !("geolocation" in navigator)) {
      setGeo({
        state: "error",
        message: "This browser does not expose device location. Enter coordinates instead.",
      });
      return;
    }

    setGeo({ state: "locating" });
    navigator.geolocation.getCurrentPosition(
      (position) => {
        addLocation({
          label: "My location",
          lat: position.coords.latitude,
          lon: position.coords.longitude,
          source: "device",
        });
        setGeo({ state: "idle" });
        setOpen(false);
      },
      (error) => {
        const message =
          error.code === error.PERMISSION_DENIED
            ? "Location permission was denied. Enter coordinates instead."
            : error.code === error.TIMEOUT
              ? "The device location request timed out. Try again or enter coordinates."
              : "The device could not determine a location. Enter coordinates instead.";
        setGeo({ state: "error", message });
      },
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 600_000 },
    );
  }

  return (
    <>
      <Popover
        open={open}
        onOpenChange={(next) => {
          setOpen(next);
          if (!next) {
            setGeo({ state: "idle" });
          }
        }}
      >
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            className="h-9 max-w-44 gap-2 px-2.5"
            aria-label={
              activeLocation
                ? `Change location. Current location: ${activeLocation.label}`
                : "Set a location"
            }
          >
            <MapPin className="size-4 shrink-0 text-brand-700" aria-hidden="true" />
            <span className="hidden truncate sm:inline">{triggerLabel}</span>
            <ChevronDown
              className="hidden size-3.5 shrink-0 text-slate-400 sm:block"
              aria-hidden="true"
            />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[min(22rem,calc(100vw-2rem))] p-0">
          <div className="border-b border-line px-4 py-3">
            <p className="text-sm font-semibold text-ink">Locations</p>
            <p className="mt-0.5 text-xs text-ink-muted">Saved on this device only.</p>
          </div>

          <div className="max-h-64 overflow-y-auto p-2">
            {locations.length === 0 ? (
              <p className="px-2 py-4 text-sm leading-relaxed text-ink-muted">
                No locations saved yet. Add coordinates or use your device location to request
                readings for a place.
              </p>
            ) : (
              <ul className="flex flex-col gap-0.5">
                {locations.map((location) => {
                  const active = location.id === activeLocation?.id;
                  return (
                    <li key={location.id} className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => {
                          setActiveLocation(location.id);
                          setOpen(false);
                        }}
                        aria-pressed={active}
                        className={cn(
                          "flex min-w-0 flex-1 items-center gap-2 rounded-lg px-2 py-2 text-left transition-colors focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none",
                          active ? "bg-brand-50" : "hover:bg-slate-50",
                        )}
                      >
                        <span
                          className={cn(
                            "inline-flex size-5 shrink-0 items-center justify-center rounded-full border",
                            active
                              ? "border-brand-700 bg-brand-700 text-white"
                              : "border-line bg-white text-transparent",
                          )}
                          aria-hidden="true"
                        >
                          <Check className="size-3" strokeWidth={3} />
                        </span>
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-medium text-ink">
                            {location.label}
                          </span>
                          <span className="block text-xs text-ink-muted">
                            {formatCoordinates(location.lat, location.lon)}
                            {location.source === "device" ? " · device" : ""}
                            {location.source === "map" ? " · map" : ""}
                          </span>
                        </span>
                      </button>
                      <button
                        type="button"
                        onClick={() => removeLocation(location.id)}
                        aria-label={`Remove ${location.label}`}
                        className="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-700 focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:outline-none"
                      >
                        <Trash2 className="size-4" aria-hidden="true" />
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          {geo.state === "error" ? (
            <div className="px-3 pb-2">
              <Alert variant="error" className="px-3 py-2 text-xs">
                <AlertDescription>{geo.message}</AlertDescription>
              </Alert>
            </div>
          ) : null}

          <Separator />
          <div className="flex flex-col gap-1 p-2">
            <Button
              type="button"
              variant="ghost"
              className="justify-start gap-2.5 px-2.5"
              onClick={useDeviceLocation}
              disabled={geo.state === "locating"}
            >
              <LocateFixed className="size-4 text-brand-700" aria-hidden="true" />
              {geo.state === "locating" ? "Locating…" : "Use my location"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              className="justify-start gap-2.5 px-2.5"
              onClick={() => {
                setOpen(false);
                setDialogOpen(true);
              }}
            >
              <Plus className="size-4 text-brand-700" aria-hidden="true" />
              Add coordinates
            </Button>
          </div>
        </PopoverContent>
      </Popover>

      <AddLocationDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </>
  );
}
