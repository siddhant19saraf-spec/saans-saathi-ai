import Link from "next/link";
import { ArrowUpRight, type LucideIcon } from "lucide-react";
import type * as React from "react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function MetricCard({
  label,
  value,
  unit,
  hint,
  icon: Icon,
  href,
  actionLabel,
  emptyLabel = "Not available",
  tone = "default",
  className,
}: {
  label: string;
  value: React.ReactNode | null;
  unit?: string;
  hint?: React.ReactNode;
  icon?: LucideIcon;
  href?: string;
  actionLabel?: string;
  emptyLabel?: string;
  tone?: "default" | "positive" | "warning" | "danger";
  className?: string;
}) {
  const hasValue = value !== null && value !== undefined && value !== "";
  const valueTone =
    tone === "positive"
      ? "text-brand-800"
      : tone === "warning"
        ? "text-amber-800"
        : tone === "danger"
          ? "text-red-800"
          : "text-ink";

  const body = (
    <>
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-medium tracking-wide text-ink-muted uppercase">{label}</p>
        {Icon ? (
          <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
            <Icon className="size-4" aria-hidden="true" />
          </span>
        ) : null}
      </div>
      <div className="mt-2 flex flex-wrap items-baseline gap-1.5">
        {hasValue ? (
          <p className={cn("metric-value text-2xl font-semibold", valueTone)}>{value}</p>
        ) : (
          <p className="text-sm font-medium text-ink-muted">{emptyLabel}</p>
        )}
        {hasValue && unit ? <span className="text-xs font-medium text-ink-muted">{unit}</span> : null}
      </div>
      {hint ? <div className="mt-1.5 text-xs leading-relaxed text-ink-muted">{hint}</div> : null}
      {href ? (
        <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-brand-700">
          {actionLabel ?? "Open"}
          <ArrowUpRight className="size-3.5" aria-hidden="true" />
        </span>
      ) : null}
    </>
  );

  return (
    <Card className={cn("h-full", href && "card-lift hover:border-brand-200 hover:shadow-raised", className)}>
      {href ? (
        <Link
          href={href}
          className="flex h-full flex-col p-4 focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 focus-visible:outline-none sm:p-5"
        >
          {body}
        </Link>
      ) : (
        <div className="flex h-full flex-col p-4 sm:p-5">{body}</div>
      )}
    </Card>
  );
}
