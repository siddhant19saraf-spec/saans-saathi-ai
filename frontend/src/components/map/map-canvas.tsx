"use client";

import "leaflet/dist/leaflet.css";

import { useEffect, useState } from "react";
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
        color: "#0f766e",
        weight: 2,
        fillColor: "#99f6e4",
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

  return (
    <MapContainer
      center={center}
      zoom={active ? 10 : 4}
      scrollWheelZoom={false}
      className="h-[26rem] w-full sm:h-[32rem]"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        maxZoom={19}
      />
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
              color: isActive ? "#065f46" : "#0f766e",
              weight: 2,
              fillColor: isActive ? "#10b981" : "#ccfbf1",
              fillOpacity: 0.95,
            }}
          >
            <Popup>
              <div className="space-y-2">
                <p className="text-xs font-semibold text-ink">{location.label}</p>
                <p className="text-xs text-ink-muted">
                  {formatCoordinates(location.lat, location.lon)}
                </p>
                <p className="text-[11px] text-slate-500">Saved place, not a monitoring station.</p>
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
  );
}
