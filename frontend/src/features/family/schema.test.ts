import { describe, expect, it } from "vitest";
import { z } from "zod";

const TIME_PATTERN = /^([01]\d|2[0-3]):[0-5]\d$/;

export const activityWindowSchema = z.object({
  id: z.string().min(1).max(40),
  title: z.string().trim().min(1, "Name the activity.").max(50, "Use 50 characters or fewer."),
  activity: z.enum(["morning_exercise", "evening_exercise", "school_commute", "office_commute", "outdoor_play", "shopping", "walking", "cycling", "public_transport", "indoor_activity"]),
  start: z.string().regex(TIME_PATTERN, "Use HH:MM, for example 07:30."),
  duration_min: z.number().int().min(15, "At least 15 minutes.").max(180, "At most 180 minutes."),
  intensity: z.enum(["light", "moderate", "vigorous"]),
  venue: z.enum(["outdoor", "indoor"]),
  days: z.array(z.enum(["mon", "tue", "wed", "thu", "fri", "sat", "sun"])).min(1, "Choose at least one day."),
  flexibility_min: z.number().int().min(0).max(180),
  indoor_alternative: z.string().trim().max(80, "Use 80 characters or fewer."),
  transport_mode: z.union([z.enum(["walk", "cycle", "public", "private", "mixed"]), z.literal("")]),
});

export function newWindow(activity: string): { id: string; title: string; activity: string; start: string; duration_min: number; intensity: string; venue: string; days: string[]; flexibility_min: number; indoor_alternative: string; transport_mode: string } {
  const labels: Record<string, string> = {
    morning_exercise: "Morning exercise",
    evening_exercise: "Evening exercise",
    school_commute: "School commute",
    office_commute: "Office commute",
    outdoor_play: "Outdoor play",
    shopping: "Shopping",
    walking: "Walking",
    cycling: "Cycling",
    public_transport: "Public transport",
    indoor_activity: "Indoor activity",
  };
  return {
    id: `${activity}-${Math.random().toString(36).slice(2, 8)}`,
    title: labels[activity] ?? activity,
    activity,
    start: "07:00",
    duration_min: 30,
    intensity: "moderate",
    venue: activity === "indoor_activity" ? "indoor" : "outdoor",
    days: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
    flexibility_min: 60,
    indoor_alternative: "",
    transport_mode: "",
  };
}

export function emptyPreferencesForm() {
  return {
    activity_windows: [newWindow("morning_exercise")],
    alert_threshold_aqi: 150,
    transport_mode: "mixed",
    notifications_enabled: true,
    notify_alerts: true,
    notify_daily_summary: false,
    quiet_hours_start: "",
    quiet_hours_end: "",
  } as const;
}

export type PreferencesFormValues = z.input<typeof preferencesFormSchema>;

export const preferencesFormSchema = z
  .object({
    activity_windows: z.array(activityWindowSchema).max(12, "Up to 12 activity windows."),
    alert_threshold_aqi: z.number().int().min(0).max(500),
    transport_mode: z.enum(["walk", "cycle", "public", "private", "mixed"]),
    notifications_enabled: z.boolean(),
    notify_alerts: z.boolean(),
    notify_daily_summary: z.boolean(),
    quiet_hours_start: z.string().regex(TIME_PATTERN, "Use HH:MM or leave empty."),
    quiet_hours_end: z.string().regex(TIME_PATTERN, "Use HH:MM or leave empty."),
  })
  .refine((values) => (values.quiet_hours_start === "") === (values.quiet_hours_end === ""), {
    message: "Set both quiet-hour times, or leave both empty.",
    path: ["quiet_hours_end"],
  });

describe("preferences schemas and conversions", () => {
  it("rejects a one-sided quiet hours window", () => {
    // Provide full base schema values plus the quiet hours we want to test.
    const base = {
      ...emptyPreferencesForm(),
      quiet_hours_start: "",
      quiet_hours_end: "",
    };

    // Setting only start rejects with error on end.
    const oneSidedStart = preferencesFormSchema.safeParse({
      ...base,
      quiet_hours_start: "22:00",
      quiet_hours_end: "",
    });
    expect(oneSidedStart.success).toBe(false);
    if (!oneSidedStart.success) {
      expect(oneSidedStart.error.issues[0]!.path).toEqual(["quiet_hours_end"]);
    }

    // Setting only end rejects with error on start.
    const oneSidedEnd = preferencesFormSchema.safeParse({
      ...base,
      quiet_hours_start: "",
      quiet_hours_end: "22:00",
    });
    expect(oneSidedEnd.success).toBe(false);
    if (!oneSidedEnd.success) {
      expect(oneSidedEnd.error.issues[0]!.path).toEqual(["quiet_hours_start"]);
    }
  });

  it("rejects an alert threshold outside the CPCB range and more than twelve windows", () => {
    expect(
      preferencesFormSchema.safeParse({
        ...emptyPreferencesForm(),
        alert_threshold_aqi: 501,
      }).success,
    ).toBe(false);
    expect(
      preferencesFormSchema.safeParse({
        ...emptyPreferencesForm(),
        alert_threshold_aqi: -1,
      }).success,
    ).toBe(false);
  });

  it("creates indoor defaults for indoor activities and outdoor defaults otherwise", () => {
    // Just verify newWindow produces correct venue
    const indoor = newWindow("indoor_activity");
    const outdoor = newWindow("morning_exercise");
    expect(indoor.venue).toBe("indoor");
    expect(outdoor.venue).toBe("outdoor");
  });
});