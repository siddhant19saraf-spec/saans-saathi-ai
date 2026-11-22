"use client";

import Link from "next/link";
import { Bell, BellOff } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useNotificationPreferences } from "@/features/settings/use-settings";

const preferenceLabels = [
  { key: "airQualityAlerts", label: "Air quality alerts" },
  { key: "routineReminders", label: "Routine reminders" },
  { key: "weeklyImpact", label: "Weekly impact summary" },
] as const;

export function Notifications() {
  const { preferences } = useNotificationPreferences();

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="relative size-9"
          aria-label="Notifications"
        >
          <Bell className="size-4" aria-hidden="true" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[min(21rem,calc(100vw-2rem))] p-0">
        <div className="flex items-center justify-between gap-2 border-b border-line px-4 py-3">
          <p className="text-sm font-semibold text-ink">Notifications</p>
          <Badge variant="neutral">Not connected</Badge>
        </div>

        <div className="flex flex-col items-center gap-2 px-6 py-8 text-center">
          <span className="inline-flex size-10 items-center justify-center rounded-full bg-slate-100 text-slate-500">
            <BellOff className="size-5" aria-hidden="true" />
          </span>
          <p className="text-sm font-medium text-ink">No notifications yet</p>
          <p className="text-xs leading-relaxed text-ink-muted">
            Alerts are only produced from connected air-quality data. This build has no delivery
            channel, so no alerts are generated or assumed.
          </p>
        </div>

        <div className="border-t border-line px-4 py-3">
          <p className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Your preferences
          </p>
          <ul className="mt-2 flex flex-col gap-1.5">
            {preferenceLabels.map(({ key, label }) => (
              <li key={key} className="flex items-center justify-between gap-3 text-xs">
                <span className="text-ink-muted">{label}</span>
                <span className="font-medium text-ink">
                  {preferences[key] ? "On (local)" : "Off"}
                </span>
              </li>
            ))}
          </ul>
          <Link
            href="/settings#notifications"
            className="mt-3 inline-flex text-xs font-semibold text-brand-700 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
          >
            Manage notification preferences
          </Link>
        </div>
      </PopoverContent>
    </Popover>
  );
}
