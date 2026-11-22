"use client";

import { Menu } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { SidebarNav } from "@/components/navigation/sidebar-nav";

import { Logo } from "../layout/logo";

export function MobileNav() {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="size-9 lg:hidden"
          aria-label="Open navigation menu"
        >
          <Menu className="size-4" aria-hidden="true" />
        </Button>
      </DialogTrigger>
      <DialogContent className="top-0 left-0 h-dvh max-h-dvh w-80 max-w-[85vw] translate-x-0 translate-y-0 flex-col rounded-none rounded-r-2xl border-y-0 border-l-0 p-0">
        <DialogTitle className="sr-only">Navigation</DialogTitle>
        <div className="flex h-full min-h-0 flex-col">
          <div className="border-b border-line px-5 py-5 pr-12">
            <Logo />
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto px-3 py-5">
            <SidebarNav onNavigate={() => setOpen(false)} />
          </div>
          <div className="border-t border-line px-5 py-4">
            <p className="text-xs font-medium text-ink-muted">
              CPCB 2014 AQI · anonymous family profile
            </p>
            <p className="mt-1 text-[11px] text-slate-500">
              Every Breath Matters. Every Decision Counts.
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
