"use client";

import { useCallback, useMemo } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Calculator, ExternalLink, Info, Leaf, Plus, Trash2 } from "lucide-react";

import { DataState } from "@/components/shared/data-state";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FieldError, Input, Label, Select } from "@/components/ui/field";
import { Separator, Skeleton } from "@/components/ui/feedback";
import { MetricCard } from "@/components/ui/metric-card";
import { ResponsiveDataTable } from "@/components/ui/responsive-data-table";
import { SectionHeader } from "@/components/ui/section-header";
import { useApiResource, type ResourceState } from "@/features/api/resource";
import { fetchFactors, type EmissionFactor } from "@/features/impact/api";
import {
  IMPACT_ACTIVITY_TYPES,
  impactActivityFormSchema,
  labelFor,
  toImpactActivity,
  todayLocalIso,
  unitFor,
  type ImpactActivity,
  type ImpactActivityFormValues,
} from "@/features/impact/schema";
import { useImpactActivities } from "@/features/impact/use-impact";
import { formatDay, formatValue } from "@/lib/format";

export function ImpactView() {
  const { activities, add, remove, hydrated } = useImpactActivities();

  const factorLoader = useCallback((signal: AbortSignal) => fetchFactors(signal), []);
  const factors = useApiResource<EmissionFactor[]>(factorLoader);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ImpactActivityFormValues>({
    resolver: zodResolver(impactActivityFormSchema),
    defaultValues: {
      type: "walked",
      quantity: "",
      occurredOn: todayLocalIso(),
    },
  });

  const totals = useMemo(() => {
    const counts = new Map<string, { count: number; quantity: number }>();
    for (const activity of activities) {
      const current = counts.get(activity.type) ?? { count: 0, quantity: 0 };
      counts.set(activity.type, {
        count: current.count + 1,
        quantity: current.quantity + activity.quantity,
      });
    }
    return counts;
  }, [activities]);

  if (!hydrated) {
    return (
      <div aria-busy="true" aria-live="polite" className="space-y-4">
        <span className="sr-only">Loading activity log</span>
        <Skeleton className="h-96 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ImpactSummary activities={activities} factors={factors.state} />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,24rem)]">
      <div className="min-w-0 space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Log an activity</CardTitle>
            <p className="text-sm text-ink-muted">
              Recorded on this device only. Logging an activity does not compute or display an
              emission saving.
            </p>
          </CardHeader>
          <CardContent>
            <form
              noValidate
              onSubmit={handleSubmit((values) => {
                add(toImpactActivity(values));
                reset({
                  type: values.type,
                  quantity: "",
                  occurredOn: todayLocalIso(),
                });
              })}
              className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_7rem_9rem_auto] sm:items-start"
            >
              <div className="flex flex-col gap-1.5">
                <Select
                  id="impact-type"
                  aria-invalid={errors.type ? true : undefined}
                  aria-describedby={errors.type ? "impact-type-error" : undefined}
                  {...register("type")}
                >
                  {IMPACT_ACTIVITY_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </Select>
                <FieldError id="impact-type-error">{errors.type?.message}</FieldError>
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="impact-quantity">Quantity</Label>
                <Input
                  id="impact-quantity"
                  inputMode="decimal"
                  placeholder="5"
                  aria-invalid={errors.quantity ? true : undefined}
                  aria-describedby={
                    errors.quantity ? "impact-quantity-error" : "impact-quantity-hint"
                  }
                  {...register("quantity")}
                />
                <FieldError id="impact-quantity-error">{errors.quantity?.message}</FieldError>
                <p id="impact-quantity-hint" className="text-xs text-slate-500">
                  Unit follows the activity.
                </p>
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="impact-date">Date</Label>
                <Input
                  id="impact-date"
                  type="date"
                  max={todayLocalIso()}
                  aria-invalid={errors.occurredOn ? true : undefined}
                  aria-describedby={errors.occurredOn ? "impact-date-error" : undefined}
                  {...register("occurredOn")}
                />
                <FieldError id="impact-date-error">{errors.occurredOn?.message}</FieldError>
              </div>

              <div className="flex flex-col gap-1.5 sm:pt-6">
                <Button type="submit">
                  <Plus className="size-4" aria-hidden="true" />
                  Add
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle>Your log</CardTitle>
              <Badge variant="neutral">{activities.length} of 200 entries</Badge>
            </div>
            <p className="text-sm text-ink-muted">
              Newest first. Amounts are the quantities you entered, not savings.
            </p>
          </CardHeader>
          <CardContent>
            {activities.length === 0 ? (
              <EmptyState
                icon={Leaf}
                title="Nothing logged yet"
                description="Add a low-carbon trip, a work-from-home day or a planted tree. Entries remain in this browser."
                className="border-0 bg-transparent py-8"
              />
            ) : (
              <ul className="divide-y divide-line">
                {activities.map((activity) => (
                  <ActivityRow
                    key={activity.id}
                    activity={activity}
                    onRemove={() => remove(activity.id)}
                  />
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="min-w-0 space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="size-4 text-brand-700" aria-hidden="true" />
              Carbon accounting
            </CardTitle>
            <p className="text-sm text-ink-muted">
              Totals require the Impact service and its versioned factor registry. No CO₂e figure is
              computed in the browser.
            </p>
          </CardHeader>
          <CardContent>
            <DataState
              state={factors.state}
              retry={factors.retry}
              loadingLabel="Loading emission factor registry"
              unavailableTitle="Factor registry not connected"
            >
              {(list) => <FactorList factors={list} />}
            </DataState>
          </CardContent>
        </Card>

        {totals.size > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Logged by type</CardTitle>
              <p className="text-xs text-ink-muted">
                Counts of your entries. These are activity quantities, not emissions.
              </p>
            </CardHeader>
            <CardContent>
              <dl className="space-y-2">
                {IMPACT_ACTIVITY_TYPES.map((type) => {
                  const entry = totals.get(type.value);
                  if (!entry) {
                    return null;
                  }
                  return (
                    <div key={type.value} className="flex items-baseline justify-between gap-3">
                      <dt className="text-sm text-ink-muted">{type.label}</dt>
                      <dd className="text-sm font-semibold text-ink">
                        {formatValue(entry.quantity, 2)} {type.unit}
                      </dd>
                    </div>
                  );
                })}
              </dl>
            </CardContent>
          </Card>
        ) : null}

        <div className="rounded-2xl border border-brand-100 bg-brand-50/70 p-4">
          <p className="flex items-center gap-2 text-sm font-semibold text-brand-900">
            <Info className="size-4" aria-hidden="true" />
            Honest accounting
          </p>
          <p className="mt-1.5 text-xs leading-relaxed text-brand-900/80">
            Emission factors must carry a source and version. Until the registry is served, this
            page will not show a number, an annual projection or a &ldquo;kg saved&rdquo; badge.
          </p>
        </div>
      </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Units and method</CardTitle>
          <p className="text-xs text-ink-muted">
            Each entry is a quantity in the unit below. A CO₂e total would require the server to
            apply a versioned factor to every entry — this browser never multiplies the two.
          </p>
        </CardHeader>
        <CardContent>
          <ResponsiveDataTable caption="Impact activity types and their recorded units">
            <thead>
              <tr className="border-b border-line bg-surface-muted text-left">
                <th scope="col" className="px-3 py-2 font-semibold text-ink">
                  Activity
                </th>
                <th scope="col" className="px-3 py-2 font-semibold text-ink">
                  Unit
                </th>
                <th scope="col" className="px-3 py-2 font-semibold text-ink">
                  Logged
                </th>
              </tr>
            </thead>
            <tbody>
              {IMPACT_ACTIVITY_TYPES.map((type) => {
                const entry = totals.get(type.value);
                return (
                  <tr key={type.value} className="border-b border-line/60 last:border-0">
                    <td className="px-3 py-2 text-ink">{type.label}</td>
                    <td className="px-3 py-2 text-ink-muted">{type.unit}</td>
                    <td className="metric-value px-3 py-2 font-medium text-ink">
                      {entry ? formatValue(entry.quantity, 2) : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </ResponsiveDataTable>
          <p className="mt-2 text-[11px] leading-relaxed text-ink-subtle">
            A dash means no entry of that type. Units are the quantities you entered; they are not
            emission savings.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function ImpactSummary({
  activities,
  factors,
}: {
  activities: ImpactActivity[];
  factors: ResourceState<EmissionFactor[]>;
}) {
  const types = new Set(activities.map((activity) => activity.type));
  const dates = activities.map((activity) => activity.occurredOn).sort();
  const first = dates[0] ?? null;
  const last = dates[dates.length - 1] ?? null;
  const registryStatus =
    factors.status === "success"
      ? factors.data.length > 0
        ? `${factors.data.length} factors loaded`
        : "Registry returned no factors"
      : factors.status === "loading" || factors.status === "idle"
        ? "Loading registry…"
        : "Registry unavailable";

  return (
    <section aria-labelledby="impact-summary-heading" className="space-y-3">
      <SectionHeader
        id="impact-summary-heading"
        title="Impact overview"
        description="Counts and units from your own log. No emissions are calculated in this build."
      />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Logged entries"
          icon={Leaf}
          value={activities.length > 0 ? activities.length : null}
          emptyLabel="No entries yet"
          hint="Stored in this browser"
        />
        <MetricCard
          label="Activity types"
          icon={Calculator}
          value={types.size > 0 ? types.size : null}
          emptyLabel="No types yet"
          hint={`${IMPACT_ACTIVITY_TYPES.length} types available`}
        />
        <MetricCard
          label="Log window"
          icon={Info}
          value={first && last ? `${formatDay(first)} – ${formatDay(last)}` : null}
          emptyLabel="No dates yet"
          hint="Earliest and latest entry dates"
        />
        <MetricCard
          label="Factor registry"
          icon={Calculator}
          value={factors.status === "success" ? factors.data.length : null}
          unit="factors"
          emptyLabel={registryStatus}
          hint="Source and version shown beside each factor"
          tone={factors.status === "success" && factors.data.length > 0 ? "positive" : "default"}
        />
      </div>
    </section>
  );
}

function ActivityRow({ activity, onRemove }: { activity: ImpactActivity; onRemove: () => void }) {
  return (
    <li className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-ink">{labelFor(activity.type)}</p>
        <p className="mt-0.5 text-xs text-ink-muted">
          {formatValue(activity.quantity, 2)} {unitFor(activity.type)} ·{" "}
          {formatDay(activity.occurredOn)}
        </p>
      </div>
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Remove ${labelFor(activity.type)} entry from ${formatDay(activity.occurredOn)}`}
        className="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-700 focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:outline-none"
      >
        <Trash2 className="size-4" aria-hidden="true" />
      </button>
    </li>
  );
}

function FactorList({ factors }: { factors: EmissionFactor[] }) {
  if (factors.length === 0) {
    return (
      <p className="text-sm text-ink-muted">
        The registry responded with no factors, so no totals are shown.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {factors.map((factor) => (
        <div key={factor.key}>
          <div className="flex items-baseline justify-between gap-3">
            <p className="text-sm font-medium text-ink">{factor.label}</p>
            <p className="text-sm text-ink-muted">
              {formatValue(factor.value, 4)} {factor.unit}
            </p>
          </div>
          <p className="mt-0.5 text-xs text-slate-500">
            {factor.source} · v{factor.version}
            {factor.retrieved_at ? ` · retrieved ${factor.retrieved_at.slice(0, 10)}` : ""}
          </p>
          <a
            href={factor.source_url}
            target="_blank"
            rel="noreferrer noopener"
            className="mt-1 inline-flex items-center gap-1 text-xs font-semibold text-brand-800 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
          >
            Source
            <ExternalLink className="size-3" aria-hidden="true" />
          </a>
          <Separator className="mt-3" />
        </div>
      ))}
      <p className="text-xs text-slate-500">
        Values come from the server registry, including provenance. The browser applies none of
        them.
      </p>
    </div>
  );
}
