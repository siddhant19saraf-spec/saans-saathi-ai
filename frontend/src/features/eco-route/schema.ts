import { z } from "zod";

export const TRAVEL_MODES = [
  { value: "walk", label: "Walking" },
  { value: "cycle", label: "Cycling" },
  { value: "two-wheeler", label: "Two-wheeler" },
  { value: "car", label: "Car" },
  { value: "bus", label: "Bus" },
  { value: "metro", label: "Metro" },
] as const;

export type TravelMode = (typeof TRAVEL_MODES)[number]["value"];

export const ecoPreferencesSchema = z.object({
  modes: z.array(z.enum(["walk", "cycle", "two-wheeler", "car", "bus", "metro"])),
  usualDistanceKm: z.number().min(0).max(200),
});

export type EcoPreferences = z.infer<typeof ecoPreferencesSchema>;

export const DEFAULT_ECO_PREFERENCES: EcoPreferences = {
  modes: ["car"],
  usualDistanceKm: 8,
};

export const ecoPreferencesFormSchema = z.object({
  modes: z
    .array(z.enum(["walk", "cycle", "two-wheeler", "car", "bus", "metro"]))
    .min(1, "Select at least one travel mode."),
  usualDistanceKm: z
    .number({ error: "Enter a typical distance." })
    .min(0, "Distance cannot be negative.")
    .max(200, "Enter 200 km or less."),
});

export type EcoPreferencesFormValues = z.input<typeof ecoPreferencesFormSchema>;
export type EcoPreferencesFormOutput = z.output<typeof ecoPreferencesFormSchema>;
