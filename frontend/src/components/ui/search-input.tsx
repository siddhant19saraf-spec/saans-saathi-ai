"use client";

import { Search, X } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

export type SearchInputProps = React.ComponentProps<"input"> & {
  onClear?: () => void;
  containerClassName?: string;
};

export const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(function SearchInput(
  { className, containerClassName, onClear, value, ...props },
  ref,
) {
  const hasValue = typeof value === "string" && value.length > 0;
  return (
    <div className={cn("relative", containerClassName)}>
      <Search
        className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-ink-subtle"
        aria-hidden="true"
      />
      <input
        ref={ref}
        value={value}
        className={cn(
          "flex h-10 w-full rounded-lg border border-line bg-white py-2 pr-9 pl-9 text-sm text-ink shadow-xs transition-colors placeholder:text-slate-400 focus-visible:border-brand-500 focus-visible:ring-2 focus-visible:ring-brand-600/25 focus-visible:outline-none disabled:cursor-not-allowed disabled:bg-slate-50",
          className,
        )}
        {...props}
      />
      {hasValue && onClear ? (
        <button
          type="button"
          onClick={onClear}
          aria-label="Clear search"
          className="absolute top-1/2 right-2 -translate-y-1/2 rounded-md p-1 text-ink-subtle transition-colors hover:bg-slate-100 hover:text-ink focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
        >
          <X className="size-3.5" aria-hidden="true" />
        </button>
      ) : null}
    </div>
  );
});
