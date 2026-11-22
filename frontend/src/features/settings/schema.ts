import { z } from "zod";

export const notificationPreferencesSchema = z.object({
  airQualityAlerts: z.boolean(),
  routineReminders: z.boolean(),
  weeklyImpact: z.boolean(),
});

export type NotificationPreferences = z.infer<typeof notificationPreferencesSchema>;

export const DEFAULT_NOTIFICATION_PREFERENCES: NotificationPreferences = {
  airQualityAlerts: false,
  routineReminders: false,
  weeklyImpact: false,
};
