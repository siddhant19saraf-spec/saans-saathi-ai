"use client";

import { Activity } from "lucide-react";

import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/feedback";
import { useProviderHealth } from "@/features/air-quality/api";
import type { ProviderHealth } from "@/features/air-quality/schemas";

const statusMeta: Record<
  ProviderHealth["status"],
  { label: string; variant: BadgeProps["variant"] }
> = {
  ok: { label: "Available", variant: "default" },
  degraded: { label: "Degraded", variant: "warning" },
  unavailable: { label: "Unavailable", variant: "danger" },
  not_configured: { label: "Not configured", variant: "neutral" },
};

const sourceLabels: Record<ProviderHealth["source_type"], string> = {
  model_forecast: "Model data",
  ground_observation: "Ground station",
  historical_observation: "Historical data",
};

function capabilities(provider: ProviderHealth): string {
  const items = [
    provider.supports_forecast ? "forecast" : null,
    provider.supports_history ? "history" : null,
    provider.supports_stations ? "stations" : null,
  ].filter((item): item is string => item !== null);
  return items.length > 0 ? `Supports ${items.join(", ")}` : "Read-only current data";
}

export function ProviderHealthPanel() {
  const health = useProviderHealth();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="size-4 text-brand-700" aria-hidden="true" />
          Provider status
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {health.state.status === "loading" ? (
          <div aria-busy="true" aria-live="polite" className="space-y-2">
            <span className="sr-only">Loading provider status</span>
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        ) : health.state.status === "success" ? (
          <ul className="space-y-2">
            {health.state.data.providers.map((provider) => {
              const meta = statusMeta[provider.status];
              return (
                <li
                  key={provider.name}
                  className="rounded-lg border border-line bg-slate-50/60 px-3 py-2.5"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-ink">{provider.name}</p>
                    <div className="flex flex-wrap items-center gap-1.5">
                      <Badge variant="outline">{sourceLabels[provider.source_type]}</Badge>
                      <Badge variant={meta.variant}>{meta.label}</Badge>
                    </div>
                  </div>
                  <p className="mt-1 text-xs leading-relaxed text-ink-muted">{provider.detail}</p>
                  <p className="mt-1 text-[11px] text-slate-500">
                    {capabilities(provider)} · circuit {provider.circuit_state}
                  </p>
                </li>
              );
            })}
          </ul>
        ) : health.state.status === "unavailable" || health.state.status === "error" ? (
          <p className="text-sm text-ink-muted">
            Provider status could not be loaded. {health.state.message}
          </p>
        ) : (
          <p className="text-sm text-ink-muted">Provider status has not loaded yet.</p>
        )}
        <p className="text-[11px] leading-relaxed text-slate-500">
          A provider is only described as working when it responds in this environment. Model data
          and ground-station observations are never merged into one reading.
        </p>
      </CardContent>
    </Card>
  );
}
