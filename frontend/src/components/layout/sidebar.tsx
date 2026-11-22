import Link from "next/link";
import { Database, ShieldCheck } from "lucide-react";

import { SidebarNav } from "@/components/navigation/sidebar-nav";

import { Logo } from "./logo";

export function Sidebar() {
  return (
    <aside className="sticky top-0 hidden h-dvh w-[17.5rem] shrink-0 flex-col border-r border-line bg-white lg:flex">
      <div className="px-5 pt-6 pb-5">
        <Logo />
      </div>

      <div className="mx-3 mb-5 rounded-xl border border-brand-100 bg-brand-50/60 p-3">
        <div className="flex items-center gap-2">
          <Database className="size-4 shrink-0 text-brand-700" aria-hidden="true" />
          <p className="text-xs font-semibold text-brand-900">Foundation build</p>
        </div>
        <p className="mt-1.5 text-xs leading-relaxed text-brand-900/80">
          Air quality comes from labelled model data, with ground-station observations kept
          separate. Every data surface states its source.
        </p>
        <Link
          href="/settings#data-sources"
          className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-brand-800 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
        >
          Review data sources
        </Link>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-4">
        <SidebarNav />
      </div>

      <div className="border-t border-line px-5 py-4">
        <p className="flex items-center gap-2 text-xs font-medium text-ink-muted">
          <ShieldCheck className="size-4 shrink-0 text-brand-700" aria-hidden="true" />
          CPCB 2014 AQI · anonymous family profile
        </p>
        <p className="mt-1 text-[11px] text-slate-500">
          Every Breath Matters. Every Decision Counts.
        </p>
      </div>
    </aside>
  );
}
