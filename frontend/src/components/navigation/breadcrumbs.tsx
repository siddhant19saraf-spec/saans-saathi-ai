"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, House } from "lucide-react";

import { navTrail } from "./nav-config";

export function Breadcrumbs() {
  const pathname = usePathname();
  const trail = navTrail(pathname);

  if (!trail) {
    return null;
  }

  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex items-center gap-1.5 text-xs text-ink-muted">
        <li>
          <Link
            href="/"
            className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 transition-colors hover:bg-slate-100 hover:text-ink focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
          >
            <House className="size-3.5" aria-hidden="true" />
            <span className="sr-only">Home</span>
          </Link>
        </li>
        <li aria-hidden="true">
          <ChevronRight className="size-3.5 text-slate-400" />
        </li>
        <li className="hidden font-medium text-slate-500 sm:block">{trail.group}</li>
        <li aria-hidden="true" className="hidden sm:block">
          <ChevronRight className="size-3.5 text-slate-400" />
        </li>
        <li>
          <span aria-current="page" className="font-semibold text-ink">
            {trail.item.label}
          </span>
        </li>
      </ol>
    </nav>
  );
}
