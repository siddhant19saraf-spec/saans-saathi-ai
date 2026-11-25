import type * as React from "react";

import { cn } from "@/lib/utils";

export function ResponsiveDataTable({
  caption,
  children,
  className,
}: {
  caption: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "w-full overflow-x-auto rounded-xl border border-line bg-white [scrollbar-width:thin]",
        className,
      )}
    >
      <table className="w-full min-w-[34rem] border-collapse text-sm">
        <caption className="sr-only">{caption}</caption>
        {children}
      </table>
    </div>
  );
}
