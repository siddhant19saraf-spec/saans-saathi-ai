import { z } from "zod";

export const savedLocationSchema = z.object({
  id: z.string().min(1),
  label: z.string().trim().min(1).max(60),
  lat: z.number().min(-90).max(90),
  lon: z.number().min(-180).max(180),
  source: z.enum(["manual", "device", "map"]),
});

export const locationsStateSchema = z.object({
  items: z.array(savedLocationSchema).max(8),
  activeId: z.string().nullable(),
});

export type SavedLocation = z.infer<typeof savedLocationSchema>;
export type LocationsState = z.infer<typeof locationsStateSchema>;

export const DEFAULT_LOCATIONS: LocationsState = { items: [], activeId: null };

const latitude = z
  .string()
  .trim()
  .min(1, "Enter a latitude.")
  .refine((value) => {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed >= -90 && parsed <= 90;
  }, "Latitude must be between -90 and 90.");

const longitude = z
  .string()
  .trim()
  .min(1, "Enter a longitude.")
  .refine((value) => {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed >= -180 && parsed <= 180;
  }, "Longitude must be between -180 and 180.");

export const coordinateFormSchema = z.object({
  label: z
    .string()
    .trim()
    .min(1, "Enter a name for this location.")
    .max(60, "Use 60 characters or fewer."),
  latitude,
  longitude,
});

export type CoordinateFormValues = z.infer<typeof coordinateFormSchema>;

export function formatCoordinates(lat: number, lon: number): string {
  return `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`;
}

/** Third-party calls receive 2-decimal coordinates, per the blueprint. */
export function roundCoordinate(value: number): number {
  return Math.round(value * 100) / 100;
}
