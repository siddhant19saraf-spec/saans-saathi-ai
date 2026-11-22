"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

import { navGroups, settingsItem, type NavItem } from "./nav-config";

function isActive(pathname: string, item: NavItem): boolean {
  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}

function NavLink({
  item,
  active,
  onNavigate,
}: {
  item: NavItem;
  active: boolean;
  onNavigate?: () => void;
}) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={cn(
        "group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none",
        active
          ? "bg-brand-50 text-brand-900 ring-1 ring-brand-100"
          : "text-ink-muted hover:bg-slate-50 hover:text-ink",
      )}
    >
      <Icon
        className={cn(
          "size-4.5 shrink-0",
          active ? "text-brand-700" : "text-slate-400 group-hover:text-ink-muted",
        )}
        aria-hidden="true"
      />
      <span className="truncate">{item.label}</span>
    </Link>
  );
}

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav aria-label="Primary" className="flex flex-col gap-6">
      {navGroups.map((group) => (
        <div key={group.label}>
          <h2 className="mb-1.5 px-3 text-[11px] font-semibold tracking-[0.12em] text-slate-500 uppercase">
            {group.label}
          </h2>
          <ul className="flex flex-col gap-0.5">
            {group.items.map((item) => (
              <li key={item.href}>
                <NavLink item={item} active={isActive(pathname, item)} onNavigate={onNavigate} />
              </li>
            ))}
          </ul>
        </div>
      ))}
      <div>
        <h2 className="mb-1.5 px-3 text-[11px] font-semibold tracking-[0.12em] text-slate-500 uppercase">
          Workspace
        </h2>
        <ul>
          <li>
            <NavLink
              item={settingsItem}
              active={isActive(pathname, settingsItem)}
              onNavigate={onNavigate}
            />
          </li>
        </ul>
      </div>
    </nav>
  );
}
