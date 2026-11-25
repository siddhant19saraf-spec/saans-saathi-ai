"use client";

import Link from "next/link";
import { Database, PanelLeftClose, PanelLeftOpen, ShieldCheck } from "lucide-react";
import { useSyncExternalStore } from "react";

import { SidebarNav } from "@/components/navigation/sidebar-nav";
import { cn } from "@/lib/utils";

import { Logo } from "./logo";

const STORAGE_KEY = "saans.v1.sidebarCollapsed";
const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function readCollapsed(): boolean {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

function writeCollapsed(next: boolean) {
  try {
    window.localStorage.setItem(STORAGE_KEY, String(next));
  } catch {
    // Storage can be unavailable in private modes. The sidebar then stays in
    // its expanded state because the stored value remains the source of truth.
  }
  for (const listener of listeners) listener();
}

export function Sidebar() {
  const collapsed = useSyncExternalStore(subscribe, readCollapsed, () => false);

  function toggle() {
    writeCollapsed(!collapsed);
  }

  return (
    <aside
      className={cn(
        "sticky top-0 hidden h-dvh shrink-0 flex-col border-r border-line bg-white transition-[width] duration-200 ease-out lg:flex",
        collapsed ? "w-[4.75rem]" : "w-[17.5rem]",
      )}
    >
      <div
        className={cn(
          "flex items-center pt-6 pb-5",
          collapsed ? "justify-center px-3" : "justify-between px-5",
        )}
      >
        <Logo iconOnly={collapsed} compact />
        {collapsed ? null : (
          <button
            type="button"
            onClick={toggle}
            aria-label="Collapse sidebar"
            aria-expanded={true}
            title="Collapse sidebar"
            className="rounded-lg p-1.5 text-ink-subtle transition-colors hover:bg-surface-muted hover:text-ink focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
          >
            <PanelLeftClose className="size-4" aria-hidden="true" />
          </button>
        )}
      </div>

      {collapsed ? null : (
        <div className="mx-3 mb-4 rounded-xl border border-brand-100 bg-brand-50/60 p-3">
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
      )}

      <div
        className={cn(
          "min-h-0 flex-1 overflow-y-auto pb-4",
          collapsed ? "px-2" : "px-3",
        )}
      >
        <SidebarNav collapsed={collapsed} />
      </div>

      <div className={cn("border-t border-line", collapsed ? "px-2 py-3" : "px-5 py-4")}>
        {collapsed ? (
          <div className="flex flex-col items-center gap-2">
            <button
              type="button"
              onClick={toggle}
              aria-label="Expand sidebar"
              aria-expanded={false}
              title="Expand sidebar"
              className="rounded-lg p-1.5 text-ink-subtle transition-colors hover:bg-surface-muted hover:text-ink focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
            >
              <PanelLeftOpen className="size-4" aria-hidden="true" />
            </button>
            <span title="CPCB 2014 AQI · anonymous family profile">
              <ShieldCheck className="size-4 text-brand-700" aria-hidden="true" />
            </span>
          </div>
        ) : (
          <>
            <p className="flex items-center gap-2 text-xs font-medium text-ink-muted">
              <ShieldCheck className="size-4 shrink-0 text-brand-700" aria-hidden="true" />
              CPCB 2014 AQI · anonymous family profile
            </p>
            <p className="mt-1 text-[11px] text-ink-subtle">
              Every Breath Matters. Every Decision Counts.
            </p>
          </>
        )}
      </div>
    </aside>
  );
}
