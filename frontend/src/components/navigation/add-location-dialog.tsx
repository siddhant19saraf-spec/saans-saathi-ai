"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Search } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogBody,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { FieldError, Input, Label } from "@/components/ui/field";
import { fetchLocationSearch } from "@/features/air-quality/api";
import type { LocationSearchResult } from "@/features/air-quality/schemas";
import { useLocations } from "@/features/locations/location-context";
import { coordinateFormSchema, type CoordinateFormValues } from "@/features/locations/schema";
import { ApiError } from "@/lib/api/client";

type AddLocationDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initial?: { lat: number; lon: number; label?: string } | null;
  source?: "manual" | "map";
};

const EMPTY: CoordinateFormValues = { label: "", latitude: "", longitude: "" };

type SearchState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "results"; items: LocationSearchResult[] }
  | { status: "empty"; message: string }
  | { status: "error"; message: string };

function resultLabel(result: LocationSearchResult): string {
  return [result.name, result.admin1, result.country].filter(Boolean).join(", ");
}

export function AddLocationDialog({
  open,
  onOpenChange,
  initial = null,
  source = "manual",
}: AddLocationDialogProps) {
  const { addLocation, locations } = useLocations();
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<CoordinateFormValues>({
    resolver: zodResolver(coordinateFormSchema),
    defaultValues: EMPTY,
  });
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState<SearchState>({ status: "idle" });

  const initialLabel = initial?.label;
  const initialLat = initial?.lat;
  const initialLon = initial?.lon;

  useEffect(() => {
    if (!open) {
      return;
    }
    reset({
      label: initialLabel ?? "",
      latitude: initialLat === undefined ? "" : String(initialLat),
      longitude: initialLon === undefined ? "" : String(initialLon),
    });
  }, [open, initialLabel, initialLat, initialLon, reset]);

  function handleOpenChange(next: boolean) {
    if (next) {
      setQuery("");
      setSearch({ status: "idle" });
    }
    onOpenChange(next);
  }

  function onSubmit(values: CoordinateFormValues) {
    addLocation({
      label: values.label.trim(),
      lat: Number(values.latitude),
      lon: Number(values.longitude),
      source,
    });
    onOpenChange(false);
  }

  async function onSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setSearch({ status: "error", message: "Enter at least two characters to search." });
      return;
    }
    setSearch({ status: "loading" });
    const controller = new AbortController();
    try {
      const response = await fetchLocationSearch(trimmed, controller.signal, { limit: 6 });
      if (response.results.length === 0) {
        setSearch({
          status: "empty",
          message: "No matching place was found. You can enter coordinates manually.",
        });
      } else {
        setSearch({ status: "results", items: response.results });
      }
    } catch (error) {
      if (error instanceof ApiError) {
        setSearch({ status: "error", message: error.message });
      } else {
        setSearch({
          status: "error",
          message: "Location search is unavailable right now. Enter coordinates manually.",
        });
      }
    }
  }

  function choose(result: LocationSearchResult) {
    setValue("label", result.name, { shouldValidate: true });
    setValue("latitude", String(result.latitude), { shouldValidate: true });
    setValue("longitude", String(result.longitude), { shouldValidate: true });
    setSearch({ status: "idle" });
    setQuery("");
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent aria-describedby="add-location-description">
        <DialogHeader>
          <DialogTitle>Add a location</DialogTitle>
          <DialogDescription id="add-location-description">
            Saved on this device only. Coordinates are rounded before they are sent to the
            air-quality service.
          </DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="mb-4 flex flex-col gap-2 border-b border-line pb-4">
            <form onSubmit={onSearch} className="flex flex-col gap-2">
              <Label htmlFor="city-search">Search for a city or place</Label>
              <div className="flex gap-2">
                <Input
                  id="city-search"
                  autoComplete="off"
                  placeholder="e.g. Pune or Delhi"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                />
                <Button type="submit" variant="outline" disabled={search.status === "loading"}>
                  <Search className="size-4" aria-hidden="true" />
                  Search
                </Button>
              </div>
            </form>
            <p className="text-xs leading-relaxed text-ink-muted">
              Search results come from the Open-Meteo geocoding service. Choosing a result only
              fills the fields below; nothing is saved until you select Save location.
            </p>

            <div aria-live="polite">
              {search.status === "loading" ? (
                <p className="text-sm text-ink-muted">Searching…</p>
              ) : null}
              {search.status === "empty" || search.status === "error" ? (
                <p className="text-sm text-ink-muted">{search.message}</p>
              ) : null}
              {search.status === "results" ? (
                <ul className="flex flex-col gap-1">
                  {search.items.map((result) => (
                    <li key={result.id}>
                      <button
                        type="button"
                        onClick={() => choose(result)}
                        className="w-full rounded-lg border border-line px-3 py-2 text-left text-sm text-ink transition-colors hover:bg-slate-50 focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
                      >
                        <span className="font-medium">{resultLabel(result)}</span>
                        <span className="mt-0.5 block text-xs text-ink-muted">
                          {result.latitude.toFixed(3)}°, {result.longitude.toFixed(3)}°
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          </div>

          <form noValidate onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="location-label">Location name</Label>
              <Input
                id="location-label"
                autoComplete="off"
                placeholder="e.g. Home, Office"
                aria-invalid={errors.label ? true : undefined}
                aria-describedby={errors.label ? "location-label-error" : undefined}
                {...register("label")}
              />
              <FieldError id="location-label-error">{errors.label?.message}</FieldError>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="location-latitude">Latitude</Label>
                <Input
                  id="location-latitude"
                  inputMode="decimal"
                  autoComplete="off"
                  placeholder="19.076"
                  aria-invalid={errors.latitude ? true : undefined}
                  aria-describedby={
                    errors.latitude ? "location-latitude-error" : "location-coordinate-hint"
                  }
                  {...register("latitude")}
                />
                <FieldError id="location-latitude-error">{errors.latitude?.message}</FieldError>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="location-longitude">Longitude</Label>
                <Input
                  id="location-longitude"
                  inputMode="decimal"
                  autoComplete="off"
                  placeholder="72.877"
                  aria-invalid={errors.longitude ? true : undefined}
                  aria-describedby={
                    errors.longitude ? "location-longitude-error" : "location-coordinate-hint"
                  }
                  {...register("longitude")}
                />
                <FieldError id="location-longitude-error">{errors.longitude?.message}</FieldError>
              </div>
            </div>

            <p id="location-coordinate-hint" className="text-xs leading-relaxed text-ink-muted">
              Decimal degrees, for example 19.0760 and 72.8777. Up to{" "}
              {Math.max(8 - locations.length, 0)} more locations can be saved. No measurements are
              created locally; coordinates are rounded before they are sent to the air-quality
              service.
            </p>

            <div className="flex flex-wrap justify-end gap-2 pt-1">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                Save location
              </Button>
            </div>
          </form>
        </DialogBody>
      </DialogContent>
    </Dialog>
  );
}

export function AddLocationButton({
  label = "Add location",
  initial,
  source = "manual",
  variant = "outline",
  size = "default",
  className,
}: {
  label?: string;
  initial?: { lat: number; lon: number; label?: string } | null;
  source?: "manual" | "map";
  variant?: "default" | "outline" | "secondary" | "ghost";
  size?: "default" | "sm" | "lg";
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button
        type="button"
        variant={variant}
        size={size}
        className={className}
        onClick={() => setOpen(true)}
      >
        {label}
      </Button>
      <AddLocationDialog open={open} onOpenChange={setOpen} initial={initial} source={source} />
    </>
  );
}
