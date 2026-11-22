"use client";

import { ArrowRight, Clock, Info, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDateTime, formatValue, titleCase } from "@/lib/format";
import type { FamilyRecommendation } from "@/features/family/schema";

const ACTION_VARIANT: Record<
  FamilyRecommendation["recommended_action"],
  "default" | "neutral" | "warning" | "danger"
> = {
  proceed: "default",
  reduce_exposure: "warning",
  reschedule: "warning",
  move_indoor: "warning",
  avoid_outdoor: "danger",
  check_back: "neutral",
};

function sourceLabel(recommendation: FamilyRecommendation): string {
  const context = recommendation.relevant_pollution_context;
  if (context.forecast_only) {
    return "Forecast PM2.5 only — not a ground measurement";
  }
  if (context.source_type === "ground_observation") {
    return "Ground observation";
  }
  if (context.source_type === "model_forecast") {
    return "Modelled forecast";
  }
  return "Validated provider data";
}

export function RecommendationCard({ recommendation }: { recommendation: FamilyRecommendation }) {
  const context = recommendation.relevant_pollution_context;

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base">{recommendation.activity_title}</CardTitle>
            <p className="mt-0.5 text-xs text-ink-muted">
              {titleCase(recommendation.activity)} · generated{" "}
              {formatDateTime(recommendation.generated_at)}
            </p>
          </div>
          <Badge variant={ACTION_VARIANT[recommendation.recommended_action]}>
            {recommendation.action_label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <p className="leading-relaxed text-ink">{recommendation.reason}</p>

        {recommendation.alternative_activity ? (
          <div className="flex items-start gap-2 rounded-lg border border-line bg-slate-50/70 px-3 py-2">
            <ArrowRight className="mt-0.5 size-4 shrink-0 text-brand-700" aria-hidden="true" />
            <div>
              <p className="text-xs font-semibold text-ink">Alternative</p>
              <p className="text-xs leading-relaxed text-ink-muted">
                {recommendation.alternative_activity}
              </p>
            </div>
          </div>
        ) : null}

        {recommendation.suggested_time || recommendation.suggested_at ? (
          <div className="flex items-start gap-2">
            <Clock className="mt-0.5 size-4 shrink-0 text-brand-700" aria-hidden="true" />
            <p className="text-xs leading-relaxed text-ink-muted">
              Lower-forecast window:{" "}
              <span className="font-semibold text-ink">
                {recommendation.suggested_time ??
                  formatDateTime(recommendation.suggested_at ?? null)}
              </span>
              {recommendation.suggested_at
                ? ` on ${formatDateTime(recommendation.suggested_at)}`
                : null}
              . Forecast timing can change.
            </p>
          </div>
        ) : null}

        <div className="rounded-lg border border-line px-3 py-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={context.forecast_only || context.stale ? "warning" : "neutral"}>
              {sourceLabel(recommendation)}
            </Badge>
            {context.stale ? <Badge variant="warning">Stale reading</Badge> : null}
          </div>
          <dl className="mt-2 grid gap-1 text-xs sm:grid-cols-2">
            <div>
              <dt className="text-ink-muted">CPCB AQI</dt>
              <dd className="font-medium text-ink">
                {context.aqi === null
                  ? "Not available"
                  : `${context.aqi}${context.category ? ` · ${titleCase(context.category)}` : ""}`}
              </dd>
            </div>
            <div>
              <dt className="text-ink-muted">PM2.5</dt>
              <dd className="font-medium text-ink">
                {context.pm2_5 === null
                  ? "Not available"
                  : `${formatValue(context.pm2_5, 1)} µg/m³`}
              </dd>
            </div>
            <div>
              <dt className="text-ink-muted">Provider</dt>
              <dd className="font-medium text-ink">{context.provider ?? "None"}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Method</dt>
              <dd className="font-medium text-ink">{context.guidance_basis_label}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Observed</dt>
              <dd className="font-medium text-ink">{formatDateTime(context.observed_at)}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Reading age</dt>
              <dd className="font-medium text-ink">
                {context.age_minutes === null ? "Not reported" : `${context.age_minutes} minutes`}
              </dd>
            </div>
          </dl>
          {context.aqi_unavailable_reason ? (
            <p className="mt-2 text-xs leading-relaxed text-amber-900">
              {context.aqi_unavailable_reason}
            </p>
          ) : null}
          <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
            {recommendation.data_source}
            {context.attribution.length > 0 ? ` · ${context.attribution.join(" · ")}` : ""}
          </p>
        </div>

        {recommendation.uncertainty_information.length > 0 ? (
          <div className="flex items-start gap-2">
            <Info className="mt-0.5 size-4 shrink-0 text-slate-500" aria-hidden="true" />
            <ul className="list-disc space-y-0.5 pl-4 text-xs leading-relaxed text-ink-muted">
              {recommendation.uncertainty_information.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="flex items-start gap-2 border-t border-line pt-3">
          <ShieldAlert className="mt-0.5 size-4 shrink-0 text-slate-500" aria-hidden="true" />
          <div className="text-[11px] leading-relaxed text-slate-500">
            <p>
              Rule {recommendation.rule_id} · {recommendation.rule_version} · Confidence{" "}
              {recommendation.confidence}
            </p>
            <details className="mt-1">
              <summary className="cursor-pointer font-medium text-ink-muted">
                Evidence and attribution
              </summary>
              <ul className="mt-1 space-y-1">
                {recommendation.evidence.map((item) => (
                  <li key={item.source}>
                    <span className="font-medium text-ink-muted">{item.source}:</span> {item.note}
                  </li>
                ))}
              </ul>
            </details>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
