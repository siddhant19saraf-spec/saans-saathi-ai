"use client";

import Link from "next/link";
import { BookOpen, Database, Settings2, UserRound } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparatorLine,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function UserMenu() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Open profile menu"
          className="flex items-center gap-2 rounded-full border border-line bg-white p-1 text-left transition-colors hover:bg-slate-50 focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 focus-visible:outline-none md:pr-3"
        >
          <span className="inline-flex size-7 items-center justify-center rounded-full bg-brand-700 text-white">
            <UserRound className="size-4" aria-hidden="true" />
          </span>
          <span className="hidden flex-col leading-tight md:flex">
            <span className="text-xs font-semibold text-ink">Guest workspace</span>
            <span className="text-[10px] text-ink-muted">Local only</span>
          </span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel>
          Guest workspace
          <span className="mt-0.5 block text-xs font-normal text-ink-muted">
            No account is connected. Profiles and plans stay on this device.
          </span>
        </DropdownMenuLabel>
        <DropdownMenuSeparatorLine />
        <DropdownMenuItem asChild>
          <Link href="/settings">
            <Settings2 className="size-4 text-slate-400" aria-hidden="true" />
            Settings
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/settings#data-sources">
            <Database className="size-4 text-slate-400" aria-hidden="true" />
            Data sources &amp; privacy
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/#about">
            <BookOpen className="size-4 text-slate-400" aria-hidden="true" />
            About this build
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
