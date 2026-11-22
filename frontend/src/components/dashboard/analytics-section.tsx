"use client";

import { useState } from "react";

import { LineTrendChart } from "@/components/charts/line-trend-chart";
import { DataState } from "@/components/shared/data-state";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAirForecast, useAirHistory } from "@/features/air-quality/api";
import type { SavedLocation } from "@/features/locations/schema";
import { formatDay, formatHour, formatValue } from "@/lib/format";

type TabValue = "forecast" | "history";

export function AnalyticsSection({ location }: { location: SavedLocation }) {
  const [tab, setTab] = useState<TabValue>("forecast");
  const forecast = useAirForecast(location, 24);
  const history = useAirHistory(tab === "history" ? location : null, 7);

  return (
    <section aria-labelledby="analytics-heading" className="space-y-4">
      <div>
        <h2 id="analytics-heading" className="text-lg font-semibold text-ink">
          Trends &amp; forecast
        </h2>
        <p className="mt-0.5 text-sm text-ink-muted">
          Charts render only from provider responses. Unavailable responses never become sample
          curves.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>PM2.5 over time</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={tab} onValueChange={(value) => setTab(value as TabValue)}>
            <TabsList aria-label="Trend view">
              <TabsTrigger value="forecast">24-hour forecast</TabsTrigger>
              <TabsTrigger value="history">7-day history</TabsTrigger>
            </TabsList>

            <TabsContent value="forecast">
              <DataState
                state={forecast.state}
                retry={forecast.retry}
                loadingLabel="Loading hourly forecast"
                unavailableTitle="Hourly forecast is not available"
              >
                {(data) => {
                  const points = data.hourly.map((point) => ({
                    label: formatHour(point.time),
                    value: point.pm2_5 ?? null,
                  }));
                  const values = points.flatMap((point) =>
                    point.value === null ? [] : [point.value],
                  );

                  return (
                    <div className="space-y-3">
                      <LineTrendChart data={points} label="PM2.5 forecast" unit="µg/m³" />
                      {values.length > 0 ? (
                        <dl className="grid grid-cols-3 gap-2">
                          <div className="rounded-lg border border-line bg-slate-50 px-3 py-2">
                            <dt className="text-[11px] text-slate-500">Lowest</dt>
                            <dd className="text-sm font-semibold text-ink">
                              {formatValue(Math.min(...values), 1)} µg/m³
                            </dd>
                          </div>
                          <div className="rounded-lg border border-line bg-slate-50 px-3 py-2">
                            <dt className="text-[11px] text-slate-500">Average</dt>
                            <dd className="text-sm font-semibold text-ink">
                              {formatValue(
                                values.reduce((sum, value) => sum + value, 0) / values.length,
                                1,
                              )}{" "}
                              µg/m³
                            </dd>
                          </div>
                          <div className="rounded-lg border border-line bg-slate-50 px-3 py-2">
                            <dt className="text-[11px] text-slate-500">Highest</dt>
                            <dd className="text-sm font-semibold text-ink">
                              {formatValue(Math.max(...values), 1)} µg/m³
                            </dd>
                          </div>
                        </dl>
                      ) : (
                        <p className="text-sm text-ink-muted">
                          The provider returned no PM2.5 values for the forecast window.
                        </p>
                      )}
                      {data.provenance?.attribution.length ? (
                        <p className="text-[11px] text-slate-500">
                          Source: {data.provenance.provider} ·{" "}
                          {data.provenance.source_type === "model_forecast"
                            ? "model-based forecast"
                            : data.provenance.source_type === "ground_observation"
                              ? "ground-station observation"
                              : "provider data"}
                          {" · "}
                          {data.provenance.attribution.join(" · ")}
                        </p>
                      ) : null}
                    </div>
                  );
                }}
              </DataState>
            </TabsContent>

            <TabsContent value="history">
              <DataState
                state={history.state}
                retry={history.retry}
                loadingLabel="Loading daily history"
                unavailableTitle="Historical air quality is not available"
              >
                {(data) => {
                  const points = data.daily.map((point) => ({
                    label: formatDay(point.date),
                    value: point.pm2_5 ?? null,
                  }));

                  return (
                    <div className="space-y-3">
                      <LineTrendChart data={points} label="PM2.5 daily history" unit="µg/m³" />
                      <p className="text-xs leading-relaxed text-ink-muted">
                        Reported history from the provider. Missing days are left empty rather than
                        interpolated.
                      </p>
                      {data.provenance?.attribution.length ? (
                        <p className="text-[11px] text-slate-500">
                          Source: {data.provenance.provider} ·{" "}
                          {data.provenance.source_type === "model_forecast"
                            ? "model-based historical data"
                            : "provider history"}
                          {" · "}
                          {data.provenance.attribution.join(" · ")}
                        </p>
                      ) : null}
                    </div>
                  );
                }}
              </DataState>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </section>
  );
}
