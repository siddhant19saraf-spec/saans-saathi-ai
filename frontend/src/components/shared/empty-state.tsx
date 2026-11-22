import type { LucideIcon } from "lucide-react";
import type * as React from "react";

import { cn } from "@/lib/utils";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-2xl border border-dashed border-line bg-white/70 px-6 py-12 text-center",
        className,
      )}
    >
      <span className="mb-4 inline-flex size-12 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
        <Icon className="size-6" aria-hidden="true" />
      </span>
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      <div className="mt-2 max-w-md text-sm leading-relaxed text-ink-muted">{description}</div>
      {action ? <div className="mt-5 flex flex-wrap justify-center gap-2">{action}</div> : null}
    </div>
  );
}
