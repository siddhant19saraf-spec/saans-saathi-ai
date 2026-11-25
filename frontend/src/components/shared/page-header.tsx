import type * as React from "react";

import { cn } from "@/lib/utils";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
}: {
  eyebrow?: string;
  title: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-4 border-b border-line pb-6 md:flex-row md:items-end md:justify-between md:gap-8",
        className,
      )}
    >
      <div className="min-w-0">
        {eyebrow ? (
          <p className="mb-2 flex items-center gap-2 text-[11px] font-semibold tracking-[0.16em] text-brand-700 uppercase">
            <span aria-hidden="true" className="h-px w-5 bg-brand-300" />
            {eyebrow}
          </p>
        ) : null}
        <h1 className="text-[1.75rem] leading-tight font-semibold tracking-[-0.025em] text-ink sm:text-[2rem]">
          {title}
        </h1>
        {description ? (
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-ink-muted sm:text-[0.9375rem]">
            {description}
          </p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex shrink-0 flex-wrap items-center gap-2 md:pb-0.5">{actions}</div>
      ) : null}
    </div>
  );
}
