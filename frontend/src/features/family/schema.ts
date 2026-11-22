import { z } from "zod";

export const ageBandSchema = z.enum(["0-5", "6-12", "13-17", "18-59", "60+"]);
export type AgeBand = z.infer<typeof ageBandSchema>;

export const healthFlagSchema = z.enum(["asthma", "allergy", "copd", "heart", "pregnant"]);
export type HealthFlag = z.infer<typeof healthFlagSchema>;

export const dwellingSchema = z.enum([
  "apartment_ground",
  "apartment_upper",
  "independent",
  "other",
]);
export const cookingFuelSchema = z.enum(["lpg", "png", "induction", "biomass", "mixed", "other"]);

export const intensitySchema = z.enum(["light", "moderate", "vigorous"]);
export const venueSchema = z.enum(["outdoor", "indoor"]);
export const transportModeSchema = z.enum(["walk", "cycle", "public", "private", "mixed"]);
export const weekdaySchema = z.enum(["mon", "tue", "wed", "thu", "fri", "sat", "sun"]);

export const activityTypeSchema = z.enum([
  "morning_exercise",
  "evening_exercise",
  "school_commute",
  "office_commute",
  "outdoor_play",
  "shopping",
  "walking",
  "cycling",
  "public_transport",
  "indoor_activity",
]);
export type ActivityType = z.infer<typeof activityTypeSchema>;

export const AGE_BAND_OPTIONS: { value: AgeBand; label: string }[] = [
  { value: "0-5", label: "0–5 years" },
  { value: "6-12", label: "6–12 years" },
  { value: "13-17", label: "13–17 years" },
  { value: "18-59", label: "18–59 years" },
  { value: "60+", label: "60 years and older" },
];

export const HEALTH_FLAG_OPTIONS: { value: HealthFlag; label: string }[] = [
  { value: "asthma", label: "Asthma or reactive airways" },
  { value: "allergy", label: "Seasonal allergy" },
  { value: "copd", label: "COPD or another chronic lung condition" },
  { value: "heart", label: "Heart condition" },
  { value: "pregnant", label: "Pregnancy" },
];

export const HEALTH_FLAG_LABELS: Record<HealthFlag, string> = Object.fromEntries(
  HEALTH_FLAG_OPTIONS.map((option) => [option.value, option.label]),
) as Record<HealthFlag, string>;

export const ACTIVITY_OPTIONS: { value: ActivityType; label: string }[] = [
  { value: "morning_exercise", label: "Morning exercise" },
  { value: "evening_exercise", label: "Evening exercise" },
  { value: "school_commute", label: "School commute" },
  { value: "office_commute", label: "Office commute" },
  { value: "outdoor_play", label: "Outdoor play" },
  { value: "shopping", label: "Shopping" },
  { value: "walking", label: "Walking" },
  { value: "cycling", label: "Cycling" },
  { value: "public_transport", label: "Public transport" },
  { value: "indoor_activity", label: "Indoor activity" },
];

export const ACTIVITY_LABELS: Record<ActivityType, string> = Object.fromEntries(
  ACTIVITY_OPTIONS.map((option) => [option.value, option.label]),
) as Record<ActivityType, string>;

export const WEEKDAY_OPTIONS: { value: z.infer<typeof weekdaySchema>; label: string }[] = [
  { value: "mon", label: "Mon" },
  { value: "tue", label: "Tue" },
  { value: "wed", label: "Wed" },
  { value: "thu", label: "Thu" },
  { value: "fri", label: "Fri" },
  { value: "sat", label: "Sat" },
  { value: "sun", label: "Sun" },
];

export const DWELLING_OPTIONS: { value: z.infer<typeof dwellingSchema>; label: string }[] = [
  { value: "apartment_upper", label: "Apartment, upper floor" },
  { value: "apartment_ground", label: "Apartment, ground floor" },
  { value: "independent", label: "Independent house" },
  { value: "other", label: "Other" },
];

export const COOKING_FUEL_OPTIONS: { value: z.infer<typeof cookingFuelSchema>; label: string }[] = [
  { value: "lpg", label: "LPG cylinder" },
  { value: "png", label: "Piped natural gas" },
  { value: "induction", label: "Electric or induction" },
  { value: "biomass", label: "Wood or biomass" },
  { value: "mixed", label: "Mixed fuels" },
  { value: "other", label: "Other" },
];

export const TRANSPORT_LABELS: Record<z.infer<typeof transportModeSchema>, string> = {
  walk: "Walking",
  cycle: "Cycling",
  public: "Public transport",
  private: "Private vehicle",
  mixed: "Mixed",
};

export const TIME_PATTERN = /^([01]\d|2[0-3]):[0-5]\d$/;

const memberSchema = z.object({
  id: z.string(),
  age_band: ageBandSchema,
  health_flags: z.array(healthFlagSchema),
  created_at: z.string(),
});

export const familyProfileSchema = z.object({
  id: z.string(),
  name: z.string(),
  size: z.number().int(),
  lat: z.number().nullable(),
  lon: z.number().nullable(),
  city: z.string().nullable(),
  timezone: z.string(),
  dwelling: z.string(),
  cooking_fuel: z.string(),
  has_purifier: z.boolean(),
  purifier_cadr: z.number().nullable(),
  room_area_m2: z.number().nullable(),
  ceiling_m: z.number().nullable(),
  members: z.array(memberSchema),
  has_children: z.boolean(),
  has_older_adults: z.boolean(),
  has_health_flags: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type FamilyProfile = z.infer<typeof familyProfileSchema>;
export type FamilyMember = z.infer<typeof memberSchema>;

export type ProfileInput = {
  name: string;
  lat: number;
  lon: number;
  city: string | null;
  timezone: string;
  dwelling: z.infer<typeof dwellingSchema>;
  cooking_fuel: z.infer<typeof cookingFuelSchema>;
  has_purifier: boolean;
  purifier_cadr: number | null;
  room_area_m2: number | null;
  members: { age_band: AgeBand; health_flags: HealthFlag[] }[];
};

function numericText(min: number, max: number, label: string) {
  return z
    .string()
    .trim()
    .min(1, `Enter ${label}.`)
    .refine((value) => Number.isFinite(Number(value)), `${label} must be a number.`)
    .refine((value) => {
      const parsed = Number(value);
      return parsed >= min && parsed <= max;
    }, `${label} must be between ${min} and ${max}.`);
}

function optionalNumericText(min: number, max: number, label: string) {
  return z
    .string()
    .trim()
    .refine((value) => {
      if (value === "") {
        return true;
      }
      const parsed = Number(value);
      return Number.isFinite(parsed) && parsed >= min && parsed <= max;
    }, `${label} must be empty or between ${min} and ${max}.`);
}

export const profileFormSchema = z
  .object({
    name: z
      .string()
      .trim()
      .min(2, "Enter a household name with at least 2 characters.")
      .max(80, "Use 80 characters or fewer."),
    city: z.string().trim().max(120, "Use 120 characters or fewer."),
    lat: numericText(-90, 90, "latitude"),
    lon: numericText(-180, 180, "longitude"),
    timezone: z.string().trim().min(1, "Choose a timezone."),
    dwelling: dwellingSchema,
    cooking_fuel: cookingFuelSchema,
    has_purifier: z.boolean(),
    purifier_cadr: optionalNumericText(50, 1500, "Purifier CADR"),
    room_area_m2: optionalNumericText(5, 300, "Room area"),
    health_consent: z.boolean(),
    members: z
      .array(
        z.object({
          age_band: ageBandSchema,
          health_flags: z.array(healthFlagSchema),
        }),
      )
      .min(1, "Add at least one household member.")
      .max(12, "A household can have up to 12 members."),
  })
  .superRefine((values, ctx) => {
    const usesFlags = values.members.some((member) => member.health_flags.length > 0);
    if (usesFlags && !values.health_consent) {
      ctx.addIssue({
        code: "custom",
        path: ["health_consent"],
        message: "Grant health-data consent to save health flags, or remove them.",
      });
    }
  });

export type ProfileFormValues = z.input<typeof profileFormSchema>;

export function emptyProfileForm(): ProfileFormValues {
  return {
    name: "",
    city: "",
    lat: "",
    lon: "",
    timezone: "Asia/Kolkata",
    dwelling: "apartment_upper",
    cooking_fuel: "lpg",
    has_purifier: false,
    purifier_cadr: "",
    room_area_m2: "",
    health_consent: false,
    members: [{ age_band: "18-59", health_flags: [] }],
  };
}

export function profileToForm(profile: FamilyProfile, healthConsent: boolean): ProfileFormValues {
  return {
    name: profile.name,
    city: profile.city ?? "",
    lat: profile.lat === null ? "" : String(profile.lat),
    lon: profile.lon === null ? "" : String(profile.lon),
    timezone: profile.timezone,
    dwelling: (dwellingSchema.safeParse(profile.dwelling).data ??
      "apartment_upper") as ProfileInput["dwelling"],
    cooking_fuel: (cookingFuelSchema.safeParse(profile.cooking_fuel).data ??
      "lpg") as ProfileInput["cooking_fuel"],
    has_purifier: profile.has_purifier,
    purifier_cadr: profile.purifier_cadr === null ? "" : String(profile.purifier_cadr),
    room_area_m2: profile.room_area_m2 === null ? "" : String(profile.room_area_m2),
    health_consent: healthConsent || profile.has_health_flags,
    members: profile.members.map((member) => ({
      age_band: member.age_band,
      health_flags: member.health_flags,
    })),
  };
}

export function toProfileInput(values: ProfileFormValues): ProfileInput {
  return {
    name: values.name.trim(),
    lat: Number(values.lat),
    lon: Number(values.lon),
    city: values.city.trim() || null,
    timezone: values.timezone.trim(),
    dwelling: values.dwelling,
    cooking_fuel: values.cooking_fuel,
    has_purifier: values.has_purifier,
    purifier_cadr:
      values.has_purifier && values.purifier_cadr.trim() !== ""
        ? Number(values.purifier_cadr)
        : null,
    room_area_m2: values.room_area_m2.trim() === "" ? null : Number(values.room_area_m2),
    members: values.members.map((member) => ({
      age_band: member.age_band,
      health_flags: member.health_flags,
    })),
  };
}

export const activityWindowSchema = z.object({
  id: z.string().min(1).max(40),
  title: z.string().trim().min(1, "Name the activity.").max(50, "Use 50 characters or fewer."),
  activity: activityTypeSchema,
  start: z.string().regex(TIME_PATTERN, "Use HH:MM, for example 07:30."),
  duration_min: z.number().int().min(15, "At least 15 minutes.").max(180, "At most 180 minutes."),
  intensity: intensitySchema,
  venue: venueSchema,
  days: z.array(weekdaySchema).min(1, "Choose at least one day."),
  flexibility_min: z.number().int().min(0).max(180),
  indoor_alternative: z.string().trim().max(80, "Use 80 characters or fewer."),
  transport_mode: z.union([transportModeSchema, z.literal("")]),
});
export type ActivityWindow = z.infer<typeof activityWindowSchema>;

export const preferencesFormSchema = z
  .object({
    activity_windows: z.array(activityWindowSchema).max(12, "Up to 12 activity windows."),
    alert_threshold_aqi: z.number().int().min(0).max(500),
    transport_mode: transportModeSchema,
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

export type PreferencesFormValues = z.input<typeof preferencesFormSchema>;

export type PreferencesInput = {
  locale: string;
  activity_windows: {
    id: string;
    title: string;
    activity: ActivityType;
    start: string;
    duration_min: number;
    intensity: z.infer<typeof intensitySchema>;
    venue: z.infer<typeof venueSchema>;
    days: z.infer<typeof weekdaySchema>[];
    flexibility_min: number;
    indoor_alternative: string | null;
    transport_mode: z.infer<typeof transportModeSchema> | null;
  }[];
  alert_threshold_aqi: number;
  transport_mode: z.infer<typeof transportModeSchema>;
  notifications_enabled: boolean;
  notify_alerts: boolean;
  notify_daily_summary: boolean;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
};

export type FamilyPreferences = Omit<PreferencesInput, "locale"> & {
  locale: string;
  household_id: string;
  created_at: string;
  updated_at: string;
};

export function newWindow(activity: ActivityType): ActivityWindow {
  const label = ACTIVITY_LABELS[activity];
  return {
    id: `${activity}-${Math.random().toString(36).slice(2, 8)}`,
    title: label,
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

export function emptyPreferencesForm(): PreferencesFormValues {
  return {
    activity_windows: [newWindow("morning_exercise")],
    alert_threshold_aqi: 150,
    transport_mode: "mixed",
    notifications_enabled: true,
    notify_alerts: true,
    notify_daily_summary: false,
    quiet_hours_start: "",
    quiet_hours_end: "",
  };
}

export function preferencesToForm(preferences: FamilyPreferences): PreferencesFormValues {
  return {
    activity_windows: preferences.activity_windows.map((window) => ({
      ...window,
      indoor_alternative: window.indoor_alternative ?? "",
      transport_mode: window.transport_mode ?? "",
    })),
    alert_threshold_aqi: preferences.alert_threshold_aqi,
    transport_mode: preferences.transport_mode,
    notifications_enabled: preferences.notifications_enabled,
    notify_alerts: preferences.notify_alerts,
    notify_daily_summary: preferences.notify_daily_summary,
    quiet_hours_start: preferences.quiet_hours_start ?? "",
    quiet_hours_end: preferences.quiet_hours_end ?? "",
  };
}

export function toPreferencesInput(values: PreferencesFormValues): PreferencesInput {
  return {
    locale: "en-IN",
    activity_windows: values.activity_windows.map((window) => ({
      id: window.id,
      title: window.title.trim(),
      activity: window.activity,
      start: window.start,
      duration_min: window.duration_min,
      intensity: window.intensity,
      venue: window.venue,
      days: window.days,
      flexibility_min: window.flexibility_min,
      indoor_alternative: window.indoor_alternative.trim() || null,
      transport_mode: window.transport_mode === "" ? null : window.transport_mode,
    })),
    alert_threshold_aqi: values.alert_threshold_aqi,
    transport_mode: values.transport_mode,
    notifications_enabled: values.notifications_enabled,
    notify_alerts: values.notify_alerts,
    notify_daily_summary: values.notify_daily_summary,
    quiet_hours_start: values.quiet_hours_start === "" ? null : values.quiet_hours_start,
    quiet_hours_end: values.quiet_hours_end === "" ? null : values.quiet_hours_end,
  };
}

export const sourceTypeSchema = z.enum([
  "ground_observation",
  "model_forecast",
  "historical_observation",
]);

export const pollutionContextSchema = z.object({
  provider: z.string().nullable(),
  source_type: sourceTypeSchema.nullable(),
  aqi: z.number().int().nullable(),
  category: z.string().nullable(),
  pm2_5: z.number().nullable(),
  pm10: z.number().nullable(),
  observed_at: z.string().nullable(),
  fetched_at: z.string().nullable(),
  age_minutes: z.number().int().nullable(),
  stale: z.boolean(),
  forecast_used: z.boolean(),
  forecast_only: z.boolean(),
  guidance_basis: z.enum(["cpcb_aqi", "pm25_band", "none"]),
  guidance_basis_label: z.string(),
  aqi_unavailable_reason: z.string().nullable().optional(),
  attribution: z.array(z.string()),
});
export type PollutionContext = z.infer<typeof pollutionContextSchema>;

export const recommendationEvidenceSchema = z.object({
  source: z.string(),
  note: z.string(),
});

export const familyRecommendationSchema = z.object({
  recommendation_id: z.string(),
  activity: activityTypeSchema,
  activity_title: z.string(),
  recommended_action: z.enum([
    "proceed",
    "reduce_exposure",
    "reschedule",
    "move_indoor",
    "avoid_outdoor",
    "check_back",
  ]),
  action_label: z.string(),
  reason: z.string(),
  relevant_pollution_context: pollutionContextSchema,
  alternative_activity: z.string().nullable().optional(),
  suggested_time: z.string().nullable().optional(),
  suggested_at: z.string().nullable().optional(),
  data_source: z.string(),
  attribution: z.array(z.string()),
  generated_at: z.string(),
  uncertainty_information: z.array(z.string()),
  evidence: z.array(recommendationEvidenceSchema),
  rule_id: z.string(),
  rule_version: z.string(),
  severity: z.enum(["good", "satisfactory", "moderate", "poor", "very_poor", "severe", "info"]),
  confidence: z.enum(["high", "medium", "low"]),
});
export type FamilyRecommendation = z.infer<typeof familyRecommendationSchema>;

export const aiExplanationSchema = z.object({
  status: z.enum(["available", "unavailable", "rejected"]),
  text: z.string().nullable().optional(),
  model: z.string().nullable().optional(),
  reason: z.string().nullable().optional(),
});

export const recommendationBatchSchema = z.object({
  household_id: z.string(),
  generated_at: z.string(),
  rules_version: z.string(),
  pollution_context: pollutionContextSchema,
  recommendations: z.array(familyRecommendationSchema),
  ai_explanation: aiExplanationSchema,
  disclaimer: z.string(),
});
export type FamilyRecommendationBatch = z.infer<typeof recommendationBatchSchema>;

export const recommendationListSchema = z.object({
  items: z.array(familyRecommendationSchema),
  limit: z.number().int(),
  offset: z.number().int(),
});
export type FamilyRecommendationList = z.infer<typeof recommendationListSchema>;

export const preferencesResponseSchema = z.object({
  household_id: z.string(),
  locale: z.string(),
  activity_windows: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      activity: activityTypeSchema,
      start: z.string(),
      duration_min: z.number().int(),
      intensity: intensitySchema,
      venue: venueSchema,
      days: z.array(weekdaySchema),
      flexibility_min: z.number().int(),
      indoor_alternative: z.string().nullable(),
      transport_mode: transportModeSchema.nullable(),
    }),
  ),
  alert_threshold_aqi: z.number().int(),
  transport_mode: transportModeSchema,
  notifications_enabled: z.boolean(),
  notify_alerts: z.boolean(),
  notify_daily_summary: z.boolean(),
  quiet_hours_start: z.string().nullable(),
  quiet_hours_end: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type FamilyPreferencesResponse = z.infer<typeof preferencesResponseSchema>;
