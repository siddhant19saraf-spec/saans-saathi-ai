"use client";

import type * as React from "react";

import { LocationProvider } from "@/features/locations/location-context";

import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <LocationProvider>
      <div className="flex min-h-dvh">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar />
          <main
            id="main-content"
            tabIndex={-1}
            className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 focus:outline-none sm:px-6 sm:py-8 lg:px-8"
          >
            {children}
          </main>
          <footer className="border-t border-line bg-white/70">
            <div className="mx-auto flex w-full max-w-6xl flex-col gap-1 px-4 py-4 text-xs text-ink-muted sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
              <p>SAANS SAATHI AI · environmental intelligence for everyday breathing.</p>
              <p>CPCB 2014 AQI · data surfaces disclose their source.</p>
            </div>
          </footer>
        </div>
      </div>
    </LocationProvider>
  );
}
