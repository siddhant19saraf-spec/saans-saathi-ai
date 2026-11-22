"use client";

import { AlertCircle, CloudOff } from "lucide-react";

import { AqiDial } from "@/components/air-quality/aqi-dial";
import { SeverityBadge } from "@/components/air-quality/severity-badge";
import { ComparisonBarChart } from "@/components/charts/comparison-bar-chart";
import { DataState } from "@/components/shared/data-state";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ResourceState } from "@/features/api/resource";
import type { AirCurrent } from "@/features/air-quality/schemas";
import { pollutantMeta, severityMeta } from "@/features/air-quality/severity";
import { formatCoordinates, type SavedLocation } from "@/features/locations/schema";
import { formatValue } from "@/lib/format";

import { PollutantGrid } from "./pollutant-grid";
import { ProvenancePanel } from "./provenance-panel";

export function CurrentAirSection({
  location,
  state,
  retry,
}: {
  location: SavedLocation;
  state: ResourceState<AirCurrent>;
  retry: () => void;
}) {
  return (
    <section aria-labelledby="current-heading" className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="current-heading" className="text-lg font-semibold text-ink">
            Current conditions
          </h2>
          <p className="mt-0.5 text-sm text-ink-muted">
            {location.label} · {formatCoordinates(location.lat, location.lon)}
          </p>
        </div>
        <Badge variant="neutral">CPCB 2014 National AQI</Badge>
      </div>

      <DataState
        state={state}
        retry={retry}
        loadingLabel="Loading current air quality"
        unavailableTitle="Current air quality is not available"
      >
        {(data) => <CurrentAirContent data={data} location={location} />}
      </DataState>
    </section>
  );
}

function CurrentAirContent({ data, location }: { data: AirCurrent; location: SavedLocation }) {
  const aqi = data.cpcb_aqi;
  const category = aqi?.category ?? null;
  const meta = category ? severityMeta[category] : null;
  const sourceLabel =
    data.provenance.source_type === "ground_observation"
      ? "Ground-station observation"
      : data.provenance.source_type === "historical_observation"
        ? "Historical observation"
        : data.provenance.source_type === "model_forecast"
          ? "Model-based forecast"
          : null;

  const comparison = pollutantMeta.flatMap((pollutant) => {
    const value = data.reading[pollutant.key];
    return value === null || value === undefined ? [] : [{ label: pollutant.label, value }];
  });

  const providerValues = [
    { label: "US AQI", value: data.provider_aqi?.us ?? null },
    { label: "European AQI", value: data.provider_aqi?.european ?? null },
  ].filter((entry) => entry.value !== null);

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="flex flex-wrap items-center gap-2">
            CPCB Air Quality Index
            {sourceLabel ? <Badge variant="outline">{sourceLabel}</Badge> : null}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center gap-3">
          <AqiDial value={aqi?.value ?? null} category={category} partial={aqi?.partial ?? false} />
          <SeverityBadge category={category} showRange />

          {meta ? <p className="text-center text-sm text-ink-muted">{meta.summary}</p> : null}

          {aqi ? (
            <div className="w-full space-y-2">
              <dl className="flex flex-wrap items-center justify-center gap-2 text-xs">
                <div className="rounded-lg border border-line bg-slate-50 px-2.5 py-1.5">
                  <dt className="text-slate-500">Dominant pollutant</dt>
                  <dd className="font-semibold text-ink">{aqi.dominant_pollutant}</dd>
                </div>
                <div className="rounded-lg border border-line bg-slate-50 px-2.5 py-1.5">
                  <dt className="text-slate-500">Method</dt>
                  <dd className="font-semibold text-ink">{aqi.method}</dd>
                </div>
              </dl>
              <p className="text-center text-[11px] leading-relaxed text-slate-500">
                Coverage: {aqi.coverage.length > 0 ? aqi.coverage.join(", ") : "none reported"}
              </p>
              {aqi.basis ? (
                <p className="text-center text-[11px] leading-relaxed text-slate-500">
                  Basis: {aqi.basis}
                </p>
              ) : null}
            </div>
          ) : (
            <Alert variant="neutral" className="w-full">
              <CloudOff className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
              <AlertDescription>
                {data.aqi_unavailable_reason ?? (
                  <>
                    A CPCB AQI could not be computed because the required pollutants were not
                    reported. Raw pollutant values are shown instead.
                  </>
                )}
              </AlertDescription>
            </Alert>
          )}

          {aqi?.partial ? (
            <Alert variant="warning" className="w-full">
              <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
              <AlertDescription>
                Partial coverage: one or more pollutants are missing from the index. The category is
                shown as partial rather than complete.
              </AlertDescription>
            </Alert>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Pollutant concentrations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <PollutantGrid reading={data.reading} />
          <p className="text-xs leading-relaxed text-ink-muted">
            Latest reported values in the units shown, with observation time and source listed
            below. A dash means the provider did not report that pollutant — SAANS SAATHI does not
            fill gaps with estimates.
          </p>
        </CardContent>
      </Card>

      {data.provider_aqi ? (
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Provider AQI — a different scale</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-2">
              {providerValues.length > 0 ? (
                providerValues.map((entry) => (
                  <Badge key={entry.label} variant="outline" className="px-3 py-1 text-sm">
                    {entry.label}: <strong className="ml-1">{formatValue(entry.value)}</strong>
                  </Badge>
                ))
              ) : (
                <p className="text-sm text-ink-muted">
                  The provider did not return a US or European index for this hour.
                </p>
              )}
            </div>
            <p className="text-xs leading-relaxed text-ink-muted">{data.provider_aqi.note}</p>
            <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-950">
              US and European AQI values use different breakpoints from the CPCB index. They are
              shown for comparison only and are never converted into a CPCB category.
            </p>
          </CardContent>
        </Card>
      ) : null}

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Pollutant comparison</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {comparison.length === 0 ? (
            <p className="text-sm text-ink-muted">
              No pollutant values were reported, so there is nothing to chart.
            </p>
          ) : (
            <>
              <ComparisonBarChart
                data={comparison}
                label="Latest reported concentration"
                unit="µg/m³"
              />
              <p className="text-xs leading-relaxed text-ink-muted">
                Raw concentrations share an axis for orientation only; different pollutants are not
                directly comparable. CO is shown here in µg/m³ while the CPCB index uses mg/m³.
              </p>
            </>
          )}
        </CardContent>
      </Card>

      <div className="lg:col-span-2">
        <ProvenancePanel provenance={data.provenance} location={location} />
      </div>
    </div>
  );
}
