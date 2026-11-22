import Link from "next/link";
import { Wind } from "lucide-react";

import { cn } from "@/lib/utils";

export function Logo({
  href = "/",
  compact = false,
  className,
}: {
  href?: string;
  compact?: boolean;
  className?: string;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex items-center gap-2.5 rounded-lg focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 focus-visible:outline-none",
        className,
      )}
    >
      <span
        aria-hidden="true"
        className="inline-flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-700 to-accent-700 text-white shadow-sm"
      >
        <Wind className="size-5" strokeWidth={2.1} />
      </span>
      <span className="flex flex-col leading-none">
        <span className="text-sm font-semibold tracking-tight text-ink">
          SAANS <span className="text-brand-700">SAATHI</span> AI
        </span>
        {compact ? null : (
          <span
            aria-hidden="true"
            className="mt-1 text-[10px] font-medium tracking-[0.18em] text-ink-muted uppercase"
          >
            Air intelligence
          </span>
        )}
      </span>
    </Link>
  );
}
