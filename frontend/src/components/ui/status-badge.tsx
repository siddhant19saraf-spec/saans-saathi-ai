import {
  AlertTriangle,
  CheckCircle2,
  CircleHelp,
  Info,
  MinusCircle,
  XCircle,
  type LucideIcon,
} from "lucide-react";
import type * as React from "react";

import { cn } from "@/lib/utils";

export type StatusTone =
  | "positive"
  | "info"
  | "warning"
  | "danger"
  | "neutral"
  | "stale"
  | "unavailable";

const TONES: Record<StatusTone, { className: string; icon: LucideIcon }> = {
  positive: {
    className: "border-brand-200 bg-brand-50 text-brand-800",
    icon: CheckCircle2,
  },
  info: { className: "border-sky-200 bg-sky-50 text-sky-900", icon: Info },
  warning: { className: "border-amber-200 bg-amber-50 text-amber-900", icon: AlertTriangle },
  danger: { className: "border-red-200 bg-red-50 text-red-900", icon: XCircle },
  neutral: { className: "border-line bg-surface-muted text-ink-muted", icon: CircleHelp },
  stale: { className: "border-amber-200 bg-amber-50 text-amber-900", icon: AlertTriangle },
  unavailable: { className: "border-line bg-surface-muted text-ink-muted", icon: MinusCircle },
};

export function StatusBadge({
  tone = "neutral",
  children,
  className,
  icon = true,
}: {
  tone?: StatusTone;
  children: React.ReactNode;
  className?: string;
  icon?: boolean;
}) {
  const config = TONES[tone];
  const Icon = config.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        config.className,
        className,
      )}
    >
      {icon ? <Icon className="size-3.5 shrink-0" aria-hidden="true" /> : null}
      {children}
    </span>
  );
}
