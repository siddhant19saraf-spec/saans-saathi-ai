"use client";

import Link from "next/link";
import { Menu } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

import { Logo } from "./logo";

const links = [
  { href: "/#features", label: "Features" },
  { href: "/#modules", label: "Modules" },
  { href: "/#standards", label: "Standards" },
  { href: "/#faq", label: "FAQ" },
];

export function MarketingHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-line/80 bg-canvas/85 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center gap-6 px-4 sm:px-6 lg:px-8">
        <Logo />
        <nav aria-label="Site" className="hidden md:block">
          <ul className="flex items-center gap-1">
            {links.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className="rounded-lg px-3 py-2 text-sm font-medium text-ink-muted transition-colors hover:bg-white hover:text-ink focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <Button asChild size="sm" className="hidden sm:inline-flex">
            <Link href="/dashboard">Open dashboard</Link>
          </Button>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="size-9 md:hidden"
                aria-label="Open navigation menu"
              >
                <Menu className="size-4" aria-hidden="true" />
              </Button>
            </DialogTrigger>
            <DialogContent className="top-0 right-0 left-auto h-dvh max-h-dvh w-80 max-w-[85vw] translate-x-0 translate-y-0 flex-col rounded-none rounded-l-2xl border-y-0 border-r-0 p-0">
              <DialogTitle className="sr-only">Site navigation</DialogTitle>
              <div className="flex h-full flex-col">
                <div className="border-b border-line px-5 py-5 pr-12">
                  <Logo />
                </div>
                <nav aria-label="Site" className="flex-1 px-3 py-4">
                  <ul className="flex flex-col gap-0.5">
                    {links.map((link) => (
                      <li key={link.href}>
                        <Link
                          href={link.href}
                          onClick={() => setOpen(false)}
                          className="block rounded-xl px-3 py-2.5 text-sm font-medium text-ink-muted transition-colors hover:bg-slate-50 hover:text-ink focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
                        >
                          {link.label}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </nav>
                <div className="border-t border-line p-4">
                  <Button asChild className="w-full">
                    <Link href="/dashboard" onClick={() => setOpen(false)}>
                      Open dashboard
                    </Link>
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </header>
  );
}
