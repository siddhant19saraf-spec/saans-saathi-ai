"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

import { allNavItems, navGroups, settingsItem } from "./nav-config";

const groupByHref = new Map<string, string>(
  navGroups.flatMap((group) => group.items.map((item) => [item.href, group.label] as const)),
);
groupByHref.set(settingsItem.href, "Workspace");

export function CommandSearch() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen(true);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const items = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) {
      return allNavItems;
    }
    return allNavItems.filter((item) =>
      [item.label, item.description, ...item.keywords].some((value) =>
        value.toLowerCase().includes(term),
      ),
    );
  }, [query]);

  const activeItem = items[Math.min(activeIndex, Math.max(items.length - 1, 0))] ?? null;

  function handleOpenChange(next: boolean) {
    setOpen(next);
    if (!next) {
      setQuery("");
      setActiveIndex(0);
    }
  }

  function openItem(href: string) {
    handleOpenChange(false);
    router.push(href);
  }

  function handleInputKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((current) => (items.length === 0 ? 0 : (current + 1) % items.length));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((current) =>
        items.length === 0 ? 0 : (current - 1 + items.length) % items.length,
      );
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (activeItem) {
        openItem(activeItem.href);
      }
    }
  }

  return (
    <>
      <Button
        type="button"
        variant="outline"
        onClick={() => setOpen(true)}
        aria-label="Search pages"
        className="h-9 gap-2 px-2.5 text-ink-muted sm:min-w-40 sm:justify-start"
      >
        <Search className="size-4" aria-hidden="true" />
        <span className="hidden sm:inline">Search</span>
        <kbd className="ml-auto hidden rounded border border-line bg-slate-50 px-1.5 py-0.5 font-sans text-[10px] font-medium text-slate-500 md:inline">
          Ctrl K
        </kbd>
      </Button>

      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent
          aria-describedby={undefined}
          className="top-[12%] max-w-xl translate-y-0 p-0"
          onOpenAutoFocus={(event) => {
            event.preventDefault();
            inputRef.current?.focus();
          }}
        >
          <DialogTitle className="sr-only">Search pages</DialogTitle>

          <div className="flex items-center gap-2.5 border-b border-line px-4">
            <Search className="size-4 shrink-0 text-ink-muted" aria-hidden="true" />
            <label htmlFor="command-search-input" className="sr-only">
              Search pages and tools
            </label>
            <input
              ref={inputRef}
              id="command-search-input"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setActiveIndex(0);
              }}
              onKeyDown={handleInputKeyDown}
              role="combobox"
              aria-expanded="true"
              aria-controls="command-search-results"
              aria-autocomplete="list"
              aria-activedescendant={
                activeItem ? `command-search-item-${activeItem.href}` : undefined
              }
              placeholder="Search pages and tools…"
              autoComplete="off"
              className="h-12 w-full bg-transparent text-sm text-ink placeholder:text-slate-400 focus:outline-none"
            />
          </div>

          <div className="max-h-[22rem] overflow-y-auto p-2">
            {items.length === 0 ? (
              <p className="px-3 py-8 text-center text-sm text-ink-muted">
                No pages match “{query.trim()}”. Search covers the pages in this workspace.
              </p>
            ) : (
              <ul
                id="command-search-results"
                role="listbox"
                aria-label="Pages"
                className="flex flex-col gap-0.5"
              >
                {items.map((item, index) => {
                  const Icon = item.icon;
                  const selected = index === activeIndex;
                  return (
                    <li key={item.href} role="presentation">
                      <Link
                        role="option"
                        id={`command-search-item-${item.href}`}
                        aria-selected={selected}
                        tabIndex={-1}
                        href={item.href}
                        onClick={() => handleOpenChange(false)}
                        onMouseEnter={() => setActiveIndex(index)}
                        className={cn(
                          "flex items-start gap-3 rounded-lg px-3 py-2.5",
                          selected ? "bg-brand-50" : "hover:bg-slate-50",
                        )}
                      >
                        <Icon
                          className={cn(
                            "mt-0.5 size-4 shrink-0",
                            selected ? "text-brand-700" : "text-slate-400",
                          )}
                          aria-hidden="true"
                        />
                        <span className="min-w-0">
                          <span className="flex items-center gap-2">
                            <span className="truncate text-sm font-medium text-ink">
                              {item.label}
                            </span>
                            <span className="shrink-0 text-[10px] font-medium tracking-wide text-slate-500 uppercase">
                              {groupByHref.get(item.href) ?? "Workspace"}
                            </span>
                          </span>
                          <span className="mt-0.5 block truncate text-xs text-ink-muted">
                            {item.description}
                          </span>
                        </span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          <div className="flex items-center justify-between gap-3 border-t border-line px-4 py-2.5 text-[11px] text-slate-500">
            <span>Arrow keys to move, Enter to open</span>
            <span>Esc to close</span>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
