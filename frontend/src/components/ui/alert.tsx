import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { cn } from "@/lib/utils";

const alertVariants = cva(
  "flex items-start gap-3 rounded-xl border px-4 py-3 text-sm leading-relaxed",
  {
    variants: {
      variant: {
        info: "border-sky-200 bg-sky-50 text-sky-950",
        success: "border-brand-200 bg-brand-50 text-brand-900",
        warning: "border-amber-200 bg-amber-50 text-amber-950",
        error: "border-red-200 bg-red-50 text-red-950",
        neutral: "border-line bg-slate-50 text-ink",
      },
    },
    defaultVariants: { variant: "info" },
  },
);

export type AlertProps = React.ComponentProps<"div"> & VariantProps<typeof alertVariants>;

export function Alert({ className, variant = "info", ...props }: AlertProps) {
  return (
    <div
      role={variant === "error" || variant === "warning" ? "alert" : "status"}
      className={cn(alertVariants({ variant }), className)}
      {...props}
    />
  );
}

export function AlertTitle({ className, ...props }: React.ComponentProps<"p">) {
  return <p className={cn("font-semibold", className)} {...props} />;
}

export function AlertDescription({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div className={cn("min-w-0 [&_a]:underline [&_a]:underline-offset-2", className)}>
      {props.children}
    </div>
  );
}
