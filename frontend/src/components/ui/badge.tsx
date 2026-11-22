import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "border-brand-200 bg-brand-50 text-brand-800",
        neutral: "border-line bg-slate-50 text-ink-muted",
        outline: "border-line bg-transparent text-ink-muted",
        warning: "border-amber-200 bg-amber-50 text-amber-900",
        danger: "border-red-200 bg-red-50 text-red-900",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export type BadgeProps = React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>;

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
