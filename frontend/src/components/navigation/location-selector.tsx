"use client";

import Link from "next/link";
import { Check, Loader2, MapPin, Search } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { AddLocationButton } from "@/components/navigation/add-location-dialog";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SearchInput } from "@/components/ui/search-input";
import { fetchLocationSearch } from "@/features/air-quality/api";
import type { LocationSearchResult } from "@/features/air-quality/schemas";
import { useLocations } from "@/features/locations/location-context";
import { formatCoordinates } from "@/features/locations/schema";
import { cn } from "@/lib/utils";

type SearchState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "results"; items: LocationSearchResult[] }
  | { status: "empty" }
  | { status: "error"; message: string };

function resultLabel(result: LocationSearchResult): string {
  return [result.name, result.admin1, result.country].filter(Boolean).join(", ");
}

/**
 * Location search with autocomplete, saved-place switching and a map link.
 *
 * Search uses the existing server-side geocoding endpoint. Choosing a result
 * saves the coordinates locally and makes them active; no reading is created
 * client-side.
 */
export function LocationSelector({ className }: { className?: string }) {
  const { locations, activeLocation, setActiveLocation, addLocation, hydrated } = useLocations();
  const [query, setQuery] = useState("");
  const [state, setState] = useState<SearchState>({ status: "idle" });
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [announcement, setAnnouncement] = useState("");
  const listId = useId();
  const inputId = useId();
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      return;
    }

    const timer = setTimeout(() => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setState({ status: "loading" });
      setOpen(true);

      fetchLocationSearch(trimmed, controller.signal, { limit: 6 })
        .then((response) => {
          if (controller.signal.aborted) return;
          setState(
            response.results.length > 0
              ? { status: "results", items: response.results }
              : { status: "empty" },
          );
          setActiveIndex(-1);
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) return;
          setState({
            status: "error",
            message:
              error instanceof Error && error.message
                ? error.message
                : "Location search is unavailable right now.",
          });
        });
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const results = useMemo(
    () => (state.status === "results" ? state.items : []),
    [state],
  );

  function choose(result: LocationSearchResult) {
    const saved = addLocation({
      label: resultLabel(result),
      lat: result.latitude,
      lon: result.longitude,
      source: "manual",
    });
    setQuery("");
    setState({ status: "idle" });
    setOpen(false);
    setAnnouncement(`${saved.label} is now the active location.`);
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") {
      setOpen(false);
      setActiveIndex(-1);
      return;
    }
    if (results.length === 0) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => (index + 1) % results.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => (index <= 0 ? results.length - 1 : index - 1));
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      const result = results[activeIndex];
      if (result) choose(result);
    }
  }

  return (
    <Card className={cn("overflow-visible", className)}>
      <CardHeader className="border-b border-line/70 pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="flex items-center gap-2 text-base font-semibold text-ink">
              <MapPin className="size-4 text-brand-700" aria-hidden="true" />
              Location
            </h2>
            <p className="mt-0.5 text-sm text-ink-muted">
              Search a city, switch a saved place, or pick coordinates on the map.
            </p>
          </div>
          {activeLocation ? (
            <Badge variant="neutral" className="max-w-full">
              <span className="truncate">Active · {activeLocation.label}</span>
            </Badge>
          ) : (
            <Badge variant="outline">No active location</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pt-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <label htmlFor={inputId} className="sr-only">
              Search for a city or place
            </label>
            <SearchInput
              id={inputId}
              role="combobox"
              aria-expanded={open}
              aria-controls={listId}
              aria-autocomplete="list"
              aria-activedescendant={
                activeIndex >= 0 ? `${listId}-option-${activeIndex}` : undefined
              }
              placeholder="Search a city or place…"
              autoComplete="off"
              value={query}
              onChange={(event) => {
                const next = event.target.value;
                setQuery(next);
                if (next.trim().length < 2) {
                  abortRef.current?.abort();
                  setState({ status: "idle" });
                  setOpen(false);
                  setActiveIndex(-1);
                }
              }}
              onFocus={() => {
                if (results.length > 0) setOpen(true);
              }}
              onKeyDown={onKeyDown}
              onClear={() => {
                setQuery("");
                setState({ status: "idle" });
                setOpen(false);
              }}
            />
            {open ? (
              <div className="absolute top-full right-0 left-0 z-30 mt-1.5 overflow-hidden rounded-xl border border-line bg-white shadow-raised animate-fade-in">
                <div aria-live="polite" className="sr-only">
                  {state.status === "loading"
                    ? "Searching for places"
                    : state.status === "results"
                      ? `${results.length} places found`
                      : state.status === "empty"
                        ? "No matching place found"
                        : ""}
                </div>
                {state.status === "loading" ? (
                  <p className="flex items-center gap-2 px-3 py-3 text-sm text-ink-muted">
                    <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                    Searching…
                  </p>
                ) : null}
                {state.status === "empty" ? (
                  <div className="px-3 py-3">
                    <p className="text-sm text-ink-muted">No matching place found.</p>
                    <p className="mt-0.5 text-xs text-ink-subtle">
                      Try a different spelling, or add coordinates directly.
                    </p>
                  </div>
                ) : null}
                {state.status === "error" ? (
                  <p className="px-3 py-3 text-sm text-ink-muted">
                    Search is unavailable right now. Add coordinates directly instead.
                  </p>
                ) : null}
                {state.status === "results" ? (
                  <ul id={listId} role="listbox" aria-label="Location search results">
                    {results.map((result, index) => (
                      <li key={result.id}>
                        <button
                          type="button"
                          id={`${listId}-option-${index}`}
                          role="option"
                          aria-selected={index === activeIndex}
                          onMouseEnter={() => setActiveIndex(index)}
                          onClick={() => choose(result)}
                          className={cn(
                            "flex w-full items-start justify-between gap-3 px-3 py-2.5 text-left transition-colors focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none",
                            index === activeIndex ? "bg-brand-50" : "hover:bg-surface-muted",
                          )}
                        >
                          <span className="min-w-0">
                            <span className="block truncate text-sm font-medium text-ink">
                              {result.name}
                            </span>
                            <span className="block truncate text-xs text-ink-muted">
                              {[result.admin1, result.country].filter(Boolean).join(", ") ||
                                formatCoordinates(result.latitude, result.longitude)}
                            </span>
                          </span>
                          <span className="shrink-0 text-[11px] text-ink-subtle">
                            {result.latitude.toFixed(2)}°, {result.longitude.toFixed(2)}°
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}
          </div>
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            <AddLocationButton label="Add place" size="sm" />
            <Link
              href="/map"
              className="inline-flex h-8 items-center gap-1.5 rounded-md border border-line bg-white px-3 text-xs font-medium text-ink transition-colors hover:bg-slate-50 focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
            >
              <MapPin className="size-3.5" aria-hidden="true" />
              Pick on map
            </Link>
          </div>
        </div>

        <div aria-live="polite" className="sr-only">
          {announcement}
        </div>

        {hydrated && locations.length > 0 ? (
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="mr-1 text-[11px] font-semibold tracking-wide text-ink-subtle uppercase">
              Saved
            </span>
            {locations.map((location) => {
              const active = location.id === activeLocation?.id;
              return (
                <button
                  key={location.id}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setActiveLocation(location.id)}
                  className={cn(
                    "inline-flex max-w-full items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none",
                    active
                      ? "border-brand-300 bg-brand-50 text-brand-900"
                      : "border-line bg-white text-ink-muted hover:border-brand-200 hover:text-ink",
                  )}
                >
                  {active ? (
                    <Check className="size-3 shrink-0" aria-hidden="true" />
                  ) : (
                    <MapPin className="size-3 shrink-0" aria-hidden="true" />
                  )}
                  <span className="truncate">{location.label}</span>
                </button>
              );
            })}
          </div>
        ) : hydrated ? (
          <p className="rounded-xl border border-dashed border-line bg-surface-muted/60 px-3 py-2.5 text-xs leading-relaxed text-ink-muted">
            No saved places yet. Search above, add coordinates, or pick a point on the map. A map
            point is a coordinate, not a monitoring station.
          </p>
        ) : (
          <p className="flex items-center gap-2 text-xs text-ink-muted">
            <Search className="size-3.5" aria-hidden="true" />
            Loading saved places…
          </p>
        )}
      </CardContent>
    </Card>
  );
}
