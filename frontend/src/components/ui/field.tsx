import type * as React from "react";

import { cn } from "@/lib/utils";

export function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      className={cn(
        "flex h-10 w-full rounded-lg border border-line bg-white px-3 py-2 text-sm text-ink shadow-xs transition-colors placeholder:text-slate-400 focus-visible:border-brand-500 focus-visible:ring-2 focus-visible:ring-brand-600/25 focus-visible:outline-none disabled:cursor-not-allowed disabled:bg-slate-50 disabled:opacity-70 aria-[invalid=true]:border-red-600 aria-[invalid=true]:ring-red-600/20",
        className,
      )}
      {...props}
    />
  );
}

export function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "flex min-h-24 w-full rounded-lg border border-line bg-white px-3 py-2 text-sm text-ink shadow-xs transition-colors placeholder:text-slate-400 focus-visible:border-brand-500 focus-visible:ring-2 focus-visible:ring-brand-600/25 focus-visible:outline-none disabled:cursor-not-allowed disabled:bg-slate-50 aria-[invalid=true]:border-red-600 aria-[invalid=true]:ring-red-600/20",
        className,
      )}
      {...props}
    />
  );
}

export function Select({ className, ...props }: React.ComponentProps<"select">) {
  return (
    <select
      className={cn(
        "flex h-10 w-full min-w-0 appearance-none rounded-lg border border-line bg-white px-3 py-2 text-sm text-ink shadow-xs transition-colors focus-visible:border-brand-500 focus-visible:ring-2 focus-visible:ring-brand-600/25 focus-visible:outline-none disabled:cursor-not-allowed disabled:bg-slate-50 aria-[invalid=true]:border-red-600",
        className,
      )}
      {...props}
    />
  );
}

export function Label({ className, ...props }: React.ComponentProps<"label">) {
  return (
    <label className={cn("text-sm font-medium leading-none text-ink", className)} {...props} />
  );
}

export function FieldError({ id, children }: { id: string; children?: React.ReactNode }) {
  if (!children) {
    return null;
  }
  return (
    <p id={id} role="alert" className="text-sm font-medium text-red-700">
      {children}
    </p>
  );
}
