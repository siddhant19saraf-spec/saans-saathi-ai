import { CloudOff } from "lucide-react";

import { severityMeta, type AqiCategory } from "@/features/air-quality/severity";
import { cn } from "@/lib/utils";

export function SeverityBadge({
  category,
  showRange = false,
  className,
}: {
  category: AqiCategory | null;
  showRange?: boolean;
  className?: string;
}) {
  if (!category) {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full border border-line bg-slate-50 px-2.5 py-0.5 text-xs font-medium text-ink-muted",
          className,
        )}
      >
        <CloudOff className="size-3.5" aria-hidden="true" />
        AQI unavailable
      </span>
    );
  }

  const meta = severityMeta[category];
  const Icon = meta.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        meta.badge,
        className,
      )}
    >
      <Icon className="size-3.5" aria-hidden="true" />
      {meta.label}
      {showRange ? <span className="font-normal opacity-80">· AQI {meta.range}</span> : null}
    </span>
  );
}
