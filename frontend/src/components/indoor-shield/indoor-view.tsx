"use client";

import Link from "next/link";
import { Home, Info, RotateCcw, ShieldCheck } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress, Skeleton } from "@/components/ui/feedback";
import { StatusBadge } from "@/components/ui/status-badge";
import { useIndoorChecklist } from "@/features/indoor/use-indoor";
import { INDOOR_CATEGORIES, INDOOR_CHECKLIST, type IndoorCategory } from "@/features/indoor/schema";

const CATEGORY_HINTS: Record<IndoorCategory, string> = {
  ventilation: "When and how to exchange indoor air with outside air.",
  dust: "Reduce particles that are tracked in and resuspended indoors.",
  kitchen: "Control cooking and combustion sources inside the home.",
  filtration: "Keep air-cleaning equipment working as intended.",
};

export function IndoorView() {
  const { checklist, toggle, completed, reset, hydrated } = useIndoorChecklist();

  if (!hydrated) {
    return (
      <div aria-busy="true" aria-live="polite" className="space-y-4">
        <span className="sr-only">Loading indoor checklist</span>
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  const total = INDOOR_CHECKLIST.length;
  const percent = (completed / total) * 100;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="size-4 text-brand-700" aria-hidden="true" />
              Shelter checklist
            </CardTitle>
            <div className="flex flex-wrap items-center gap-1.5">
              <StatusBadge tone="neutral">Self-reported actions, not a measurement</StatusBadge>
              <Badge variant={completed === total ? "default" : "neutral"}>
                {completed} of {total} complete
              </Badge>
            </div>
          </div>
          <p className="text-sm text-ink-muted">
            Progress is saved in this browser only. Checking an item records your own action — it is
            not a measurement of indoor air quality.
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          <Progress
            value={percent}
            label={`Checklist progress: ${completed} of ${total} items complete`}
            className="h-2"
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-slate-500">
              {completed === total
                ? "All checklist items are marked complete."
                : `${total - completed} item${total - completed === 1 ? "" : "s"} remaining.`}
            </p>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={reset}
              disabled={completed === 0}
            >
              <RotateCcw className="size-3.5" aria-hidden="true" />
              Clear checklist
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {INDOOR_CATEGORIES.map((category) => {
          const items = INDOOR_CHECKLIST.filter((item) => item.category === category.value);
          const categoryDone = items.filter((item) => checklist[item.id]).length;
          const categoryPercent = items.length > 0 ? (categoryDone / items.length) * 100 : 0;

          return (
            <Card key={category.value}>
              <CardHeader>
                <div className="flex items-center justify-between gap-2">
                  <CardTitle className="text-sm">{category.label}</CardTitle>
                  <span className="text-[11px] font-medium text-ink-muted">
                    {categoryDone}/{items.length} · {Math.round(categoryPercent)}%
                  </span>
                </div>
                <p className="text-xs text-ink-muted">{CATEGORY_HINTS[category.value]}</p>
                <Progress
                  value={categoryPercent}
                  label={`${category.label} progress: ${categoryDone} of ${items.length} complete`}
                  className="mt-2 h-1.5"
                />
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {items.map((item) => {
                    const checked = checklist[item.id] === true;
                    const descriptionId = `indoor-guidance-${item.id}`;
                    return (
                      <li key={item.id} className="rounded-xl border border-line bg-white p-3">
                        <div className="flex items-start gap-2.5">
                          <Checkbox
                            id={`indoor-${item.id}`}
                            checked={checked}
                            onCheckedChange={(value) => toggle(item.id, value === true)}
                            aria-describedby={descriptionId}
                            className="mt-0.5"
                          />
                          <div className="min-w-0">
                            <label
                              htmlFor={`indoor-${item.id}`}
                              className="cursor-pointer text-sm leading-snug font-medium text-ink"
                            >
                              {item.title}
                            </label>
                            <p
                              id={descriptionId}
                              className="mt-1 text-xs leading-relaxed text-ink-muted"
                            >
                              {item.guidance}
                            </p>
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Info className="size-4 text-brand-700" aria-hidden="true" />
            What this page does not do
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm leading-relaxed text-ink-muted">
            These are general household measures, not personalised medical advice. No indoor sensor
            is connected, so nothing here estimates indoor PM2.5, predicts filter life for your
            room, or scores your home. Use the dashboard to see the outdoor reading for your
            selected location and follow the manufacturer&apos;s instructions for any purifier.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-800 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
            >
              <Home className="size-3.5" aria-hidden="true" />
              Current outdoor air
            </Link>
            <Link
              href="/smart-routine"
              className="text-sm font-semibold text-brand-800 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
            >
              Plan outdoor activities
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
