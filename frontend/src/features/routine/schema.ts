import { z } from "zod";

export const VENUES = [
  { value: "outdoor", label: "Outdoors" },
  { value: "indoor", label: "Indoors" },
] as const;

export const INTENSITIES = [
  { value: "light", label: "Light" },
  { value: "moderate", label: "Moderate" },
  { value: "vigorous", label: "Vigorous" },
] as const;

export const timePattern = /^([01]\d|2[0-3]):[0-5]\d$/;

export const routineActivitySchema = z.object({
  id: z.string(),
  title: z.string().min(1).max(50),
  start: z.string().regex(timePattern),
  durationMin: z.number().int().min(15).max(180),
  venue: z.enum(["outdoor", "indoor"]),
  intensity: z.enum(["light", "moderate", "vigorous"]),
});

export const routineActivitiesSchema = z.array(routineActivitySchema).max(12);

export type RoutineActivity = z.infer<typeof routineActivitySchema>;

export const routineActivityFormSchema = z.object({
  title: z
    .string()
    .trim()
    .min(1, "Give the activity a name.")
    .max(50, "Use 50 characters or fewer."),
  start: z.string().regex(timePattern, "Choose a start time between 00:00 and 23:59."),
  durationMin: z
    .number({ error: "Enter a duration in minutes." })
    .int("Duration must be a whole number of minutes.")
    .min(15, "Use at least 15 minutes.")
    .max(180, "Use at most 180 minutes."),
  venue: z.enum(["outdoor", "indoor"]),
  intensity: z.enum(["light", "moderate", "vigorous"]),
});

export type RoutineActivityFormValues = z.input<typeof routineActivityFormSchema>;
export type RoutineActivityFormOutput = z.output<typeof routineActivityFormSchema>;

export function toRoutineActivity(values: RoutineActivityFormOutput): RoutineActivity {
  return {
    id:
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `activity-${Date.now()}`,
    title: values.title.trim(),
    start: values.start,
    durationMin: values.durationMin,
    venue: values.venue,
    intensity: values.intensity,
  };
}

export function sortByStart(activities: RoutineActivity[]): RoutineActivity[] {
  return [...activities].sort((a, b) => a.start.localeCompare(b.start));
}
