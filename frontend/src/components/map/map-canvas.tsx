"use client";

import "leaflet/dist/leaflet.css";

import { Loader2, TriangleAlert } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap, useMapEvents } from "react-leaflet";

import { Button } from "@/components/ui/button";
import { formatCoordinates, type SavedLocation } from "@/features/locations/schema";

const FALLBACK_CENTER: [number, number] = [21.5, 79.0];

function ClickPicker({ onPick }: { onPick: (lat: number, lon: number) => void }) {
  const [point, setPoint] = useState<[number, number] | null>(null);

  useMapEvents({
    click(event) {
      setPoint([event.latlng.lat, event.latlng.lng]);
    },
  });

  if (!point) {
    return null;
  }

  return (
    <CircleMarker
      center={point}
      radius={8}
      pathOptions={{
        color: "#195c48",
        weight: 2,
        fillColor: "#86c5a9",
        fillOpacity: 1,
      }}
    >
      <Popup>
        <div className="space-y-2">
          <p className="text-xs font-semibold text-ink">{formatCoordinates(point[0], point[1])}</p>
          <p className="text-xs text-ink-muted">
            A point on the map is a coordinate, not a monitoring station.
          </p>
          <Button
            type="button"
            size="sm"
            onClick={() => {
              onPick(point[0], point[1]);
              setPoint(null);
            }}
          >
            Use this point
          </Button>
        </div>
      </Popup>
    </CircleMarker>
  );
}

function Recenter({ location }: { location: SavedLocation | null }) {
  const map = useMap();

  useEffect(() => {
    if (location) {
      map.setView([location.lat, location.lon], Math.max(map.getZoom(), 10));
    }
  }, [location, map]);

  return null;
}

/**
 * Leaflet computes its viewport from the container size at mount. A sidebar
 * collapse, font load or responsive breakpoint can change that size without a
 * window resize, which leaves grey bands or a partially painted map. Observing
 * the container keeps the canvas in sync.
 */
function MapResize() {
  const map = useMap();

  useEffect(() => {
    const container = typeof map.getContainer === "function" ? map.getContainer() : null;
    if (!container || typeof ResizeObserver === "undefined") {
      return;
    }
    const observer = new ResizeObserver(() => {
      map.invalidateSize({ animate: false });
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, [map]);

  return null;
}

type TileStatus = "loading" | "ready" | "error";

/**
 * Leaflet's `load` event is not reliable for cached tiles or a layer that is
 * re-created during a React remount: the images finish before React's handler
 * is attached, so the event never arrives. Reading the tile images directly
 * gives a truthful status in every case.
 */
function TileStatusWatcher({ onChange }: { onChange: (status: TileStatus) => void }) {
  const map = useMap();

  useEffect(() => {
    if (typeof map.getContainer !== "function") {
      return;
    }
    const container = map.getContainer();
    if (!container) {
      return;
    }
    let frame = 0;

    const evaluate = () => {
      const tiles = Array.from(container.querySelectorAll<HTMLImageElement>(".leaflet-tile"));
      if (tiles.length === 0) {
        return;
      }
      if (tiles.some((tile) => !tile.complete)) {
        onChange("loading");
        return;
      }
      onChange(tiles.some((tile) => tile.naturalWidth === 0) ? "error" : "ready");
    };

    const schedule = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(evaluate);
    };

    const observer = new MutationObserver(schedule);
    observer.observe(container, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["src", "class"],
    });
    // A cached image may never emit another mutation, so also re-check on a
    // slow interval until the component unmounts.
    const interval = window.setInterval(schedule, 1200);
    schedule();

    return () => {
      observer.disconnect();
      window.clearInterval(interval);
      cancelAnimationFrame(frame);
    };
  }, [map, onChange]);

  return null;
}

export function MapCanvas({
  locations,
  activeId,
  onPick,
  onActivate,
}: {
  locations: SavedLocation[];
  activeId: string | null;
  onPick: (lat: number, lon: number) => void;
  onActivate: (id: string) => void;
}) {
  const active = locations.find((location) => location.id === activeId) ?? null;
  const center: [number, number] = active ? [active.lat, active.lon] : FALLBACK_CENTER;
  const [tileStatus, setTileStatus] = useState<TileStatus>("loading");
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  const handleTileStatus = useCallback((status: TileStatus) => {
    setTileStatus(status);
    if (status === "ready") {
      setHasLoadedOnce(true);
    }
  }, []);

  return (
    <div className="relative bg-surface-muted">
      <MapContainer
        center={center}
        zoom={active ? 10 : 4}
        scrollWheelZoom={false}
        className="z-0 h-[26rem] w-full sm:h-[32rem]"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />
        <TileStatusWatcher onChange={handleTileStatus} />
        <MapResize />
        <Recenter location={active} />
        <ClickPicker onPick={onPick} />

        {locations.map((location) => {
          const isActive = location.id === activeId;
          return (
            <CircleMarker
              key={location.id}
              center={[location.lat, location.lon]}
              radius={isActive ? 9 : 6}
              pathOptions={{
                color: isActive ? "#123d31" : "#195c48",
                weight: 2,
                fillColor: isActive ? "#10b981" : "#b5ddc8",
                fillOpacity: 0.95,
              }}
            >
              <Popup>
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-ink">{location.label}</p>
                  <p className="text-xs text-ink-muted">
                    {formatCoordinates(location.lat, location.lon)}
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Saved place, not a monitoring station.
                  </p>
                  {isActive ? (
                    <p className="text-xs font-medium text-brand-800">Active location</p>
                  ) : (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => onActivate(location.id)}
                    >
                      Set as active
                    </Button>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {tileStatus === "loading" ? (
        hasLoadedOnce ? (
          <div
            aria-live="polite"
            className="pointer-events-none absolute bottom-3 left-3 flex items-center gap-2 rounded-full border border-line bg-white/95 px-3 py-1.5 text-xs font-medium text-ink-muted shadow-card"
          >
            <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
            Loading tiles…
          </div>
        ) : (
          <div
            aria-live="polite"
            className="pointer-events-none absolute inset-0 flex items-center justify-center bg-surface-muted/80"
          >
            <div className="flex items-center gap-2 rounded-full border border-line bg-white px-3 py-1.5 text-xs font-medium text-ink-muted shadow-card">
              <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
              Loading map tiles…
            </div>
          </div>
        )
      ) : null}

      {tileStatus === "error" ? (
        <div
          role="status"
          className="absolute inset-x-3 bottom-3 rounded-xl border border-amber-200 bg-white/95 px-3 py-2.5 text-xs leading-relaxed text-amber-950 shadow-raised"
        >
          <p className="flex items-center gap-1.5 font-semibold">
            <TriangleAlert className="size-3.5 shrink-0" aria-hidden="true" />
            Map tiles could not be loaded
          </p>
          <p className="mt-1">
            Check your connection. Saved places and coordinate entry remain available, and no map
            content is fabricated.{" "}
            <a
              href={`https://www.openstreetmap.org/#map=10/${center[0]}/${center[1]}`}
              target="_blank"
              rel="noreferrer noopener"
              className="font-semibold underline underline-offset-2"
            >
              Open this area on OpenStreetMap
            </a>
          </p>
        </div>
      ) : null}
    </div>
  );
}
