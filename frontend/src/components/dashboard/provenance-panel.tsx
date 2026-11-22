import { Clock3, Database, Info, MapPin, Radio } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AirProvenance, SourceType } from "@/features/air-quality/schemas";
import { formatCoordinates, type SavedLocation } from "@/features/locations/schema";
import { formatDateTime, titleCase } from "@/lib/format";

const sourceLabels: Record<SourceType, string> = {
  model_forecast: "Model-based forecast",
  ground_observation: "Ground-station observation",
  historical_observation: "Historical observation",
};

export function ProvenancePanel({
  provenance,
  location,
}: {
  provenance: AirProvenance;
  location: SavedLocation;
}) {
  const stale = provenance.freshness === "stale" || provenance.stale;
  const station = provenance.station ?? null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="size-4 text-brand-700" aria-hidden="true" />
          Source &amp; freshness
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <dl className="grid gap-3 sm:grid-cols-2">
          <div>
            <dt className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
              Provider
            </dt>
            <dd className="mt-0.5 text-sm font-medium text-ink">{provenance.provider}</dd>
          </div>
          <div>
            <dt className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
              Data source type
            </dt>
            <dd className="mt-0.5 flex items-center gap-1.5 text-sm font-medium text-ink">
              {provenance.source_type
                ? sourceLabels[provenance.source_type]
                : titleCase(provenance.kind)}
              <Badge variant={stale ? "warning" : "neutral"}>
                {stale ? "Stale" : "Within window"}
              </Badge>
            </dd>
          </div>
          <div>
            <dt className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
              Observed
            </dt>
            <dd className="mt-0.5 flex items-center gap-1.5 text-sm text-ink">
              <Clock3 className="size-3.5 text-slate-400" aria-hidden="true" />
              {formatDateTime(provenance.observed_at)}
            </dd>
          </div>
          <div>
            <dt className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
              Fetched
            </dt>
            <dd className="mt-0.5 text-sm text-ink">
              {formatDateTime(provenance.fetched_at)}
              <span className="ml-1.5 text-xs text-ink-muted">
                ({provenance.age_minutes} min old)
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
              Location
            </dt>
            <dd className="mt-0.5 flex items-center gap-1.5 text-sm text-ink">
              <MapPin className="size-3.5 text-slate-400" aria-hidden="true" />
              <span>
                {location.label} · {formatCoordinates(location.lat, location.lon)}
              </span>
            </dd>
          </div>
          {station ? (
            <div>
              <dt className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
                Monitoring station
              </dt>
              <dd className="mt-0.5 flex items-center gap-1.5 text-sm text-ink">
                <Radio className="size-3.5 text-slate-400" aria-hidden="true" />
                <span>
                  {station.name} · {station.provider}
                  {station.distance_km !== null && station.distance_km !== undefined
                    ? ` · ${station.distance_km.toFixed(1)} km away`
                    : ""}
                </span>
              </dd>
            </div>
          ) : null}
          {provenance.model ? (
            <div>
              <dt className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
                Model
              </dt>
              <dd className="mt-0.5 text-sm text-ink">{provenance.model}</dd>
            </div>
          ) : null}
        </dl>

        {provenance.source_type === "model_forecast" ? (
          <p className="rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 text-xs leading-relaxed text-sky-950">
            These values come from an atmospheric model, not a monitoring station. They are labelled
            as model-based forecast data and are not presented as measured concentrations.
          </p>
        ) : null}

        {stale ? (
          <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-950">
            This response is marked stale by the provider or freshness policy. Treat it as
            historical, not current.
          </p>
        ) : null}

        <div className="rounded-lg border border-line bg-slate-50 px-3 py-2">
          <p className="flex items-center gap-1.5 text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
            <Info className="size-3.5" aria-hidden="true" />
            Attribution
          </p>
          <ul className="mt-1 flex list-inside list-disc flex-col gap-0.5 text-xs leading-relaxed text-ink-muted">
            {provenance.attribution.map((entry) => (
              <li key={entry}>{entry}</li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
