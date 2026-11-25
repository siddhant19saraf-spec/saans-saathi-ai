"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMemo, useState } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { ArrowRight, Bike, Clock, CloudOff, Info, Leaf, MapPin, Route } from "lucide-react";

import { DataState } from "@/components/shared/data-state";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { FieldError, Input, Label } from "@/components/ui/field";
import { Separator } from "@/components/ui/feedback";
import { useApiResource } from "@/features/api/resource";
import {
  compareEcoRoute,
  originFromLocation,
  type EcoRouteComparison,
  type EcoRouteMode,
  type EcoRouteRequest,
} from "@/features/eco-route/api";
import {
  TRAVEL_MODES,
  ecoPreferencesFormSchema,
  type EcoPreferencesFormValues,
  type TravelMode,
} from "@/features/eco-route/schema";
import { useEcoPreferences } from "@/features/eco-route/use-eco";
import { coordinateFormSchema } from "@/features/locations/schema";
import { useLocations } from "@/features/locations/location-context";
import { formatValue } from "@/lib/format";

const MODE_LABELS = new Map(TRAVEL_MODES.map((mode) => [mode.value, mode.label]));

const RECOMMENDATION_LABELS: Record<string, string> = {
  carbon: "Lower carbon",
  air: "Lower exposure",
  time: "Faster",
};

export function EcoRouteView() {
  const { preferences, save, hydrated: preferencesHydrated } = useEcoPreferences();
  const { activeLocation, hydrated: locationsHydrated } = useLocations();
  const [request, setRequest] = useState<EcoRouteRequest | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [tripLabels, setTripLabels] = useState<{ origin: string; destination: string } | null>(null);

  const preferenceForm = useForm<EcoPreferencesFormValues>({
    resolver: zodResolver(ecoPreferencesFormSchema),
    defaultValues: {
      modes: preferences.modes,
      usualDistanceKm: preferences.usualDistanceKm,
    },
  });

  const tripForm = useForm<{
    label: string;
    latitude: string;
    longitude: string;
  }>({
    resolver: zodResolver(coordinateFormSchema),
    defaultValues: { label: "", latitude: "", longitude: "" },
  });

  const loader = useMemo(
    () => (request ? (signal: AbortSignal) => compareEcoRoute(request, signal) : null),
    [request],
  );
  const { state, retry } = useApiResource<EcoRouteComparison>(loader);
  const selectedModes = useWatch({ control: preferenceForm.control, name: "modes" }) ?? [];

  if (!preferencesHydrated || !locationsHydrated) {
    return (
      <div aria-busy="true" aria-live="polite" className="space-y-4">
        <span className="sr-only">Loading route preferences</span>
        <div className="h-40 animate-pulse rounded-2xl bg-slate-200/80" />
        <div className="h-96 animate-pulse rounded-2xl bg-slate-200/80" />
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,24rem)_minmax(0,1fr)]">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bike className="size-4 text-brand-700" aria-hidden="true" />
              Saved travel preferences
            </CardTitle>
            <p className="text-sm text-ink-muted">
              Stored in this browser. These modes are requested when you compare a trip.
            </p>
          </CardHeader>
          <CardContent>
            <form
              noValidate
              onSubmit={preferenceForm.handleSubmit((values) => {
                save({ modes: values.modes, usualDistanceKm: values.usualDistanceKm });
              })}
              className="space-y-4"
            >
              <fieldset
                aria-describedby={
                  preferenceForm.formState.errors.modes ? "eco-modes-error" : undefined
                }
              >
                <legend className="text-sm font-medium text-ink">Travel modes you use</legend>
                <Controller
                  control={preferenceForm.control}
                  name="modes"
                  render={({ field }) => (
                    <div className="mt-2 grid gap-2 sm:grid-cols-2">
                      {TRAVEL_MODES.map((mode) => {
                        const checked = field.value.includes(mode.value);
                        return (
                          <label
                            key={mode.value}
                            className="flex cursor-pointer items-center gap-2 rounded-lg border border-line bg-white px-2.5 py-2 text-sm text-ink"
                          >
                            <Checkbox
                              checked={checked}
                              onCheckedChange={(value) => {
                                const next =
                                  value === true
                                    ? [...field.value, mode.value]
                                    : field.value.filter((item: TravelMode) => item !== mode.value);
                                field.onChange(next);
                              }}
                            />
                            {mode.label}
                          </label>
                        );
                      })}
                    </div>
                  )}
                />
                {preferenceForm.formState.errors.modes?.message ? (
                  <p
                    id="eco-modes-error"
                    role="alert"
                    className="mt-1.5 text-sm font-medium text-red-700"
                  >
                    {preferenceForm.formState.errors.modes.message}
                  </p>
                ) : null}
              </fieldset>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="usual-distance">Usual trip distance (km)</Label>
                <Input
                  id="usual-distance"
                  type="number"
                  min={0}
                  max={200}
                  step={0.5}
                  aria-invalid={preferenceForm.formState.errors.usualDistanceKm ? true : undefined}
                  aria-describedby={
                    preferenceForm.formState.errors.usualDistanceKm
                      ? "usual-distance-error"
                      : "usual-distance-hint"
                  }
                  {...preferenceForm.register("usualDistanceKm", {
                    valueAsNumber: true,
                  })}
                />
                <FieldError id="usual-distance-error">
                  {preferenceForm.formState.errors.usualDistanceKm?.message}
                </FieldError>
                <p id="usual-distance-hint" className="text-xs text-slate-500">
                  For context only — route distance comes from the routing provider used by the
                  comparison service.
                </p>
              </div>

              <Button type="submit" variant="secondary" className="w-full">
                Save preferences
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="rounded-2xl border border-brand-100 bg-brand-50/70 p-4">
          <p className="flex items-center gap-2 text-sm font-semibold text-brand-900">
            <Info className="size-4" aria-hidden="true" />
            What we will not show
          </p>
          <p className="mt-1.5 text-xs leading-relaxed text-brand-900/80">
            No route is drawn or scored on this device. Pollution exposure is only shown when the
            comparison service returns an exposure index built from real air-quality data; otherwise
            the column stays empty.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Route className="size-4 text-brand-700" aria-hidden="true" />
              Compare a route
            </CardTitle>
            <p className="text-sm text-ink-muted">
              The server estimates distance and duration, then compares the selected modes. Nothing
              is calculated in the browser.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-xl border border-line bg-slate-50 px-3 py-2.5">
              <p className="flex items-center gap-1.5 text-xs font-semibold tracking-wide text-slate-500 uppercase">
                <MapPin className="size-3.5" aria-hidden="true" />
                Origin
              </p>
              {activeLocation ? (
                <p className="mt-1 text-sm text-ink">
                  {activeLocation.label}{" "}
                  <span className="text-xs text-ink-muted">
                    ({activeLocation.lat.toFixed(3)}, {activeLocation.lon.toFixed(3)})
                  </span>
                </p>
              ) : (
                <p className="mt-1 text-sm text-ink-muted">
                  No active location.{" "}
                  <Link
                    href="/map"
                    className="font-semibold text-brand-800 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
                  >
                    Choose one on the map
                  </Link>{" "}
                  first.
                </p>
              )}
            </div>

            <form
              noValidate
              onSubmit={tripForm.handleSubmit((values) => {
                const origin = originFromLocation(activeLocation);
                if (!origin) {
                  setFormError("Choose an active origin location before comparing.");
                  return;
                }
                const modes = preferenceForm.getValues("modes");
                if (modes.length === 0) {
                  setFormError("Select at least one travel mode in your preferences.");
                  return;
                }
                setFormError(null);
                setTripLabels({
                  origin: activeLocation?.label ?? "Origin",
                  destination: values.label,
                });
                setRequest({
                  origin,
                  destination: {
                    lat: Number(values.latitude),
                    lon: Number(values.longitude),
                  },
                  modes,
                });
              })}
              className="space-y-3"
            >
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="destination-label">Destination name</Label>
                <Input
                  id="destination-label"
                  placeholder="e.g. Office"
                  autoComplete="off"
                  aria-invalid={tripForm.formState.errors.label ? true : undefined}
                  aria-describedby={
                    tripForm.formState.errors.label ? "destination-label-error" : undefined
                  }
                  {...tripForm.register("label")}
                />
                <FieldError id="destination-label-error">
                  {tripForm.formState.errors.label?.message}
                </FieldError>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="destination-latitude">Latitude</Label>
                  <Input
                    id="destination-latitude"
                    inputMode="decimal"
                    placeholder="28.6139"
                    autoComplete="off"
                    aria-invalid={tripForm.formState.errors.latitude ? true : undefined}
                    aria-describedby={
                      tripForm.formState.errors.latitude ? "destination-latitude-error" : undefined
                    }
                    {...tripForm.register("latitude")}
                  />
                  <FieldError id="destination-latitude-error">
                    {tripForm.formState.errors.latitude?.message}
                  </FieldError>
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="destination-longitude">Longitude</Label>
                  <Input
                    id="destination-longitude"
                    inputMode="decimal"
                    placeholder="77.2090"
                    autoComplete="off"
                    aria-invalid={tripForm.formState.errors.longitude ? true : undefined}
                    aria-describedby={
                      tripForm.formState.errors.longitude
                        ? "destination-longitude-error"
                        : undefined
                    }
                    {...tripForm.register("longitude")}
                  />
                  <FieldError id="destination-longitude-error">
                    {tripForm.formState.errors.longitude?.message}
                  </FieldError>
                </div>
              </div>

              {formError ? (
                <p role="alert" className="text-xs font-medium text-red-700">
                  {formError}
                </p>
              ) : null}

              <div className="flex flex-wrap items-center gap-2">
                <Button type="submit" disabled={!activeLocation}>
                  <ArrowRight className="size-4" aria-hidden="true" />
                  Compare selected modes
                </Button>
                <span className="text-xs text-slate-500">
                  {selectedModes.length} mode
                  {selectedModes.length === 1 ? "" : "s"} requested
                </span>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <DataState
              state={state}
              retry={retry}
              loadingLabel="Comparing travel modes"
              unavailableTitle="Route comparison service not connected"
              idle={
                <div className="flex items-start gap-3 rounded-xl border border-dashed border-line px-3 py-4">
                  <CloudOff className="mt-0.5 size-4 shrink-0 text-slate-400" aria-hidden="true" />
                  <p className="text-sm text-ink-muted">
                    Enter a destination and compare. If the comparison service is not running in
                    this build, the result stays unavailable and no estimate is substituted.
                  </p>
                </div>
              }
            >
              {(comparison) => (
                <ComparisonResult comparison={comparison} labels={tripLabels} />
              )}
            </DataState>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ComparisonResult({
  comparison,
  labels,
}: {
  comparison: EcoRouteComparison;
  labels: { origin: string; destination: string } | null;
}) {
  const carbonModes = comparison.modes
    .filter((mode) => mode.recommended_for.includes("carbon"))
    .map((mode) => MODE_LABELS.get(mode.mode as TravelMode) ?? mode.mode);
  const exposureModes = comparison.modes
    .filter((mode) => mode.recommended_for.includes("air"))
    .map((mode) => MODE_LABELS.get(mode.mode as TravelMode) ?? mode.mode);
  const fastestModes = comparison.modes
    .filter((mode) => mode.recommended_for.includes("time"))
    .map((mode) => MODE_LABELS.get(mode.mode as TravelMode) ?? mode.mode);

  return (
    <div className="space-y-4">
      {labels ? (
        <div className="flex flex-wrap items-center gap-2 rounded-xl border border-line bg-surface-muted px-3 py-2.5 text-sm">
          <MapPin className="size-4 shrink-0 text-brand-700" aria-hidden="true" />
          <span className="font-medium text-ink">{labels.origin}</span>
          <ArrowRight className="size-3.5 text-ink-subtle" aria-hidden="true" />
          <span className="font-medium text-ink">{labels.destination}</span>
          <Badge variant="outline" className="ml-auto">
            {comparison.route.is_estimate ? "Estimated route" : "Provider route"}
          </Badge>
        </div>
      ) : null}

      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Badge variant="neutral">{comparison.route.distance_km.toFixed(1)} km</Badge>
        <Badge variant="neutral">
          <Clock className="size-3" aria-hidden="true" />
          {comparison.route.duration_min.toFixed(0)} min
        </Badge>
        <span className="text-xs text-ink-subtle">
          {comparison.route.is_estimate ? "Estimated by" : "Routing via"} {comparison.route.source}
        </span>
      </div>

      {carbonModes.length > 0 || exposureModes.length > 0 || fastestModes.length > 0 ? (
        <div className="grid gap-2 sm:grid-cols-3">
          <div className="rounded-xl border border-brand-100 bg-brand-50/60 px-3 py-2.5">
            <p className="text-[10px] font-semibold tracking-wide text-brand-800 uppercase">
              Lower carbon
            </p>
            <p className="mt-0.5 text-sm font-medium text-ink">
              {carbonModes.length > 0 ? carbonModes.join(", ") : "Not ranked"}
            </p>
          </div>
          <div className="rounded-xl border border-line bg-surface-muted px-3 py-2.5">
            <p className="text-[10px] font-semibold tracking-wide text-ink-subtle uppercase">
              Lower exposure
            </p>
            <p className="mt-0.5 text-sm font-medium text-ink">
              {exposureModes.length > 0 ? exposureModes.join(", ") : "Not ranked"}
            </p>
          </div>
          <div className="rounded-xl border border-line bg-surface-muted px-3 py-2.5">
            <p className="text-[10px] font-semibold tracking-wide text-ink-subtle uppercase">
              Faster
            </p>
            <p className="mt-0.5 text-sm font-medium text-ink">
              {fastestModes.length > 0 ? fastestModes.join(", ") : "Not ranked"}
            </p>
          </div>
        </div>
      ) : null}

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <caption className="sr-only">
            Carbon, exposure index and duration for each compared travel mode
          </caption>
          <thead>
            <tr className="border-b border-line text-left text-[11px] tracking-wide text-slate-500 uppercase">
              <th scope="col" className="py-2 pr-3 font-semibold">
                Mode
              </th>
              <th scope="col" className="py-2 pr-3 font-semibold">
                CO₂e
              </th>
              <th scope="col" className="py-2 pr-3 font-semibold">
                Exposure index
              </th>
              <th scope="col" className="py-2 font-semibold">
                Duration
              </th>
            </tr>
          </thead>
          <tbody>
            {comparison.modes.map((mode) => (
              <ModeRow key={mode.mode} mode={mode} />
            ))}
          </tbody>
        </table>
      </div>

      {comparison.tradeoff_note ? (
        <Alert variant="info">
          <Leaf className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <AlertDescription>{comparison.tradeoff_note}</AlertDescription>
        </Alert>
      ) : null}

      {comparison.assumptions.length > 0 ? (
        <div>
          <p className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Assumptions from the service
          </p>
          <ul className="mt-1.5 space-y-1">
            {comparison.assumptions.map((assumption) => (
              <li key={assumption.key} className="text-xs text-ink-muted">
                <code className="rounded bg-slate-100 px-1 py-0.5 text-[11px]">
                  {assumption.key}
                </code>{" "}
                = {String(assumption.value)} · {assumption.source}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <Separator />
      <p className="text-xs text-slate-500">
        Exposure index is only present when the service has air-quality data for the route. Higher
        values mean more inhaled pollution in the service&apos;s model; it is not a clinical
        measure.
      </p>
    </div>
  );
}

function ModeRow({ mode }: { mode: EcoRouteMode }) {
  return (
    <tr className="border-b border-line/70 align-top last:border-0">
      <th scope="row" className="py-2.5 pr-3 text-left font-medium text-ink">
        {MODE_LABELS.get(mode.mode as TravelMode) ?? mode.mode}
        {mode.recommended_for.length > 0 ? (
          <span className="mt-1 flex flex-wrap gap-1">
            {mode.recommended_for.map((reason) => (
              <Badge key={reason} variant="default" className="px-1.5 py-0 text-[10px]">
                {RECOMMENDATION_LABELS[reason] ?? reason}
              </Badge>
            ))}
          </span>
        ) : null}
      </th>
      <td className="py-2.5 pr-3 text-ink-muted">
        {mode.co2e_kg === null ? "Not reported" : `${formatValue(mode.co2e_kg, 2)} kg`}
      </td>
      <td className="py-2.5 pr-3 text-ink-muted">
        {mode.exposure_index === null ? "—" : `${Math.round(mode.exposure_index)} / 100`}
      </td>
      <td className="py-2.5 text-ink-muted">
        {mode.duration_min === null ? "Not reported" : `${formatValue(mode.duration_min)} min`}
      </td>
    </tr>
  );
}
