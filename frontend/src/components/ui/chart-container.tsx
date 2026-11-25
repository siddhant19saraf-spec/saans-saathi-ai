import type * as React from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function ChartContainer({
  title,
  description,
  actions,
  footer,
  children,
  className,
}: {
  title: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="border-b border-line/70 pb-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle>{title}</CardTitle>
            {description ? (
              <p className="mt-1 text-sm leading-relaxed text-ink-muted">{description}</p>
            ) : null}
          </div>
          {actions}
        </div>
      </CardHeader>
      <CardContent className="pt-4">{children}</CardContent>
      {footer ? (
        <div className="border-t border-line/70 bg-surface-muted/60 px-5 py-3 text-xs leading-relaxed text-ink-muted">
          {footer}
        </div>
      ) : null}
    </Card>
  );
}
