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
  collapsed = false,
  onNavigate,
}: {
  item: NavItem;
  active: boolean;
  collapsed?: boolean;
  onNavigate?: () => void;
}) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      title={collapsed ? item.label : undefined}
      className={cn(
        "group relative flex items-center gap-3 rounded-xl text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none",
        collapsed ? "justify-center px-2 py-2.5" : "px-3 py-2",
        active
          ? "bg-brand-50 text-brand-900 ring-1 ring-brand-100"
          : "text-ink-muted hover:bg-surface-muted hover:text-ink",
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "absolute top-1/2 left-0 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-brand-700 transition-opacity",
          active ? "opacity-100" : "opacity-0",
        )}
      />
      <Icon
        className={cn(
          "size-4.5 shrink-0",
          active ? "text-brand-700" : "text-ink-subtle group-hover:text-ink-muted",
        )}
        aria-hidden="true"
      />
      <span className={cn("truncate", collapsed && "sr-only")}>{item.label}</span>
    </Link>
  );
}

function GroupHeading({
  children,
  collapsed,
}: {
  children: React.ReactNode;
  collapsed?: boolean;
}) {
  return (
    <h2
      className={cn(
        "mb-1.5 px-3 text-[10.5px] font-semibold tracking-[0.14em] text-ink-subtle uppercase",
        collapsed && "sr-only",
      )}
    >
      {children}
    </h2>
  );
}

export function SidebarNav({
  onNavigate,
  collapsed = false,
}: {
  onNavigate?: () => void;
  collapsed?: boolean;
}) {
  const pathname = usePathname();

  return (
    <nav aria-label="Primary" className={cn("flex flex-col", collapsed ? "gap-3" : "gap-5")}>
      {navGroups.map((group, index) => (
        <div key={group.label}>
          {collapsed && index > 0 ? (
            <div aria-hidden="true" className="mx-2 mb-3 h-px bg-line" />
          ) : null}
          <GroupHeading collapsed={collapsed}>{group.label}</GroupHeading>
          <ul className="flex flex-col gap-0.5">
            {group.items.map((item) => (
              <li key={item.href}>
                <NavLink
                  item={item}
                  active={isActive(pathname, item)}
                  collapsed={collapsed}
                  onNavigate={onNavigate}
                />
              </li>
            ))}
          </ul>
        </div>
      ))}
      <div>
        {collapsed ? <div aria-hidden="true" className="mx-2 mb-3 h-px bg-line" /> : null}
        <GroupHeading collapsed={collapsed}>Preferences</GroupHeading>
        <ul>
          <li>
            <NavLink
              item={settingsItem}
              active={isActive(pathname, settingsItem)}
              collapsed={collapsed}
              onNavigate={onNavigate}
            />
          </li>
        </ul>
      </div>
    </nav>
  );
}
