"use client";

import { Info, Layers, Ruler } from "lucide-react";

import { AnalyticsSection } from "@/components/dashboard/analytics-section";
import { CurrentAirSection } from "@/components/dashboard/current-air-section";
import { LocationGate } from "@/components/dashboard/location-gate";
import { LocationSelector } from "@/components/navigation/location-selector";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/feedback";
import { useAirCurrent } from "@/features/air-quality/api";
import { useLocations } from "@/features/locations/location-context";

import { ProviderHealthPanel } from "./provider-health-panel";
import { StandardsTable } from "./standards-table";

export function AirQualityView() {
  const { activeLocation, hydrated } = useLocations();
  const current = useAirCurrent(activeLocation);

  if (!hydrated) {
    return (
      <div aria-busy="true" aria-live="polite" className="space-y-4">
        <span className="sr-only">Loading air intelligence</span>
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-72 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (!activeLocation) {
    return (
      <div className="space-y-8">
        <LocationSelector />
        <LocationGate />
      </div>
    );
  }

  return (
    <div className="space-y-9">
      <LocationSelector />
      <CurrentAirSection location={activeLocation} state={current.state} retry={current.retry} />
      <AnalyticsSection location={activeLocation} />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Ruler className="size-4 text-brand-700" aria-hidden="true" />
              How the CPCB index is computed
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-relaxed text-ink-muted">
            <p>
              The CPCB National AQI evaluates eight pollutants — PM10, PM2.5, NO₂, SO₂, CO, O₃, NH₃
              and Pb. A sub-index is computed for each pollutant with sufficient data, and the
              highest sub-index becomes the AQI.
            </p>
            <p>
              The pollutant that produces the highest sub-index is reported as the dominant
              pollutant. CO is indexed in mg/m³; particulate values use µg/m³.
            </p>
            <p>
              When required pollutants are missing, the index is flagged as partial. SAANS SAATHI
              displays the backend result and never fills gaps in the browser to complete a
              category.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Layers className="size-4 text-brand-700" aria-hidden="true" />
              Why other AQI scales are separate
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-relaxed text-ink-muted">
            <p>
              Some providers return a US or European AQI alongside the raw concentrations. Those
              indices use different breakpoints and category names from the CPCB index.
            </p>
            <p>
              When both exist, SAANS SAATHI shows the provider values in a separate, labelled card.
              A value of 100 on one scale is not the same condition as 100 on another, so no
              conversion is performed.
            </p>
            <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950">
              Categories, health context and colour are always attached to the named standard.
              Colour alone never communicates severity.
            </p>
          </CardContent>
        </Card>
      </div>

      <StandardsTable />

      <div className="grid gap-4 lg:grid-cols-2">
        <ProviderHealthPanel />

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="size-4 text-brand-700" aria-hidden="true" />
              Data limitations in this build
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-inside list-disc space-y-1.5 text-sm leading-relaxed text-ink-muted">
              <li>
                Open-Meteo values are model-based forecast data. They are labelled as such and are
                never presented as monitoring-station measurements.
              </li>
              <li>
                Ground-station observations come from OpenAQ only when an API key is configured.
                OpenAQ coverage is incomplete, so a nearby station is not guaranteed.
              </li>
              <li>
                The CPCB adapter reports an explicit unavailable status: its official data-access
                endpoint could not be verified, so no CPCB observations are requested or relabelled.
              </li>
              <li>
                A CPCB AQI is reported only when the required averaging windows and pollutant count
                are satisfied. Otherwise the response includes the reason it is unavailable.
              </li>
              <li>
                Freshness comes from the API response (observation time, fetch time, age and
                freshness flag), not from the browser clock.
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
