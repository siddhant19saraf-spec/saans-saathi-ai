"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { BellRing, Database, HardDrive, Info, MapPin, ShieldCheck, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator, Skeleton } from "@/components/ui/feedback";
import { Switch } from "@/components/ui/switch";
import { useEcoPreferences } from "@/features/eco-route/use-eco";
import { useImpactActivities } from "@/features/impact/use-impact";
import { useIndoorChecklist } from "@/features/indoor/use-indoor";
import { useLocations } from "@/features/locations/location-context";
import { useRoutineActivities } from "@/features/routine/use-routine";
import {
  DEFAULT_NOTIFICATION_PREFERENCES,
  type NotificationPreferences,
} from "@/features/settings/schema";
import { useNotificationPreferences } from "@/features/settings/use-settings";
import { removeStored, STORAGE_KEYS } from "@/features/store/storage";

const NOTIFICATION_FIELDS: {
  key: keyof NotificationPreferences;
  label: string;
  description: string;
}[] = [
  {
    key: "airQualityAlerts",
    label: "Air quality alerts",
    description: "Preference for a future alert when the selected location worsens.",
  },
  {
    key: "routineReminders",
    label: "Routine reminders",
    description: "Preference for a future reminder before a planned outdoor activity.",
  },
  {
    key: "weeklyImpact",
    label: "Weekly impact summary",
    description: "Preference for a future weekly digest of logged activities.",
  },
];

export function SettingsView() {
  const {
    preferences,
    setPreference,
    hydrated: notificationsHydrated,
  } = useNotificationPreferences();
  const { locations } = useLocations();
  const { activities: routineActivities } = useRoutineActivities();
  const { activities: impactActivities } = useImpactActivities();
  const { completed } = useIndoorChecklist();
  const { preferences: ecoPreferences } = useEcoPreferences();

  if (!notificationsHydrated) {
    return (
      <div aria-busy="true" aria-live="polite" className="space-y-4">
        <span className="sr-only">Loading settings</span>
        <Skeleton className="h-72 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const storedGroups = [
    {
      key: STORAGE_KEYS.locations,
      label: "Saved locations",
      count: locations.length,
      unit: "location",
      plural: "locations",
      detail: locations.map((location) => location.label).join(", "),
    },
    {
      key: STORAGE_KEYS.routineActivities,
      label: "SmartRoutine activities",
      count: routineActivities.length,
      unit: "activity",
      plural: "activities",
      detail: "",
    },
    {
      key: STORAGE_KEYS.impactActivities,
      label: "Impact log",
      count: impactActivities.length,
      unit: "entry",
      plural: "entries",
      detail: "",
    },
    {
      key: STORAGE_KEYS.indoorChecklist,
      label: "IndoorShield checklist",
      count: completed,
      unit: "checked item",
      plural: "checked items",
      detail: "",
    },
    {
      key: STORAGE_KEYS.ecoPreferences,
      label: "Travel preferences",
      count: ecoPreferences.modes.length,
      unit: "mode",
      plural: "modes",
      detail: ecoPreferences.modes.join(", "),
    },
    {
      key: STORAGE_KEYS.notificationPreferences,
      label: "Notification preferences",
      count: Object.values(preferences).filter(Boolean).length,
      unit: "enabled",
      plural: "enabled",
      detail: "",
    },
  ];

  return (
    <div className="space-y-8">
      <nav aria-label="Settings sections">
        <ul className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
          <li>
            <a className="text-brand-800 underline-offset-2 hover:underline" href="#notifications">
              Notifications
            </a>
          </li>
          <li>
            <a className="text-brand-800 underline-offset-2 hover:underline" href="#data-sources">
              Data sources
            </a>
          </li>
          <li>
            <a className="text-brand-800 underline-offset-2 hover:underline" href="#local-data">
              Local data
            </a>
          </li>
        </ul>
      </nav>

      <section id="notifications" aria-labelledby="notifications-heading" className="scroll-mt-24">
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle id="notifications-heading" className="flex items-center gap-2">
                <BellRing className="size-4 text-brand-700" aria-hidden="true" />
                Notifications
              </CardTitle>
              <Badge variant="neutral">Preferences only</Badge>
            </div>
            <p className="text-sm text-ink-muted">
              Choices are saved in this browser. No notification channel is connected in this build,
              so nothing is sent anywhere.
            </p>
          </CardHeader>
          <CardContent className="space-y-1">
            {NOTIFICATION_FIELDS.map((field, index) => (
              <div
                key={field.key}
                className={
                  index === 0
                    ? "flex items-start justify-between gap-4 py-3"
                    : "flex items-start justify-between gap-4 border-t border-line py-3"
                }
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-ink" id={`${field.key}-label`}>
                    {field.label}
                  </p>
                  <p className="mt-0.5 text-xs text-ink-muted" id={`${field.key}-description`}>
                    {field.description}
                  </p>
                </div>
                <Switch
                  checked={preferences[field.key]}
                  onCheckedChange={(checked) => setPreference(field.key, checked)}
                  aria-labelledby={`${field.key}-label`}
                  aria-describedby={`${field.key}-description`}
                  className="mt-1"
                />
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section id="data-sources" aria-labelledby="data-sources-heading" className="scroll-mt-24">
        <Card>
          <CardHeader>
            <CardTitle id="data-sources-heading" className="flex items-center gap-2">
              <Database className="size-4 text-brand-700" aria-hidden="true" />
              Data sources and methods
            </CardTitle>
            <p className="text-sm text-ink-muted">
              What each surface would use when the backend services are configured. Methods never
              mix AQI standards.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <SourceRow
              icon={<MapPin className="size-4" aria-hidden="true" />}
              title="Air quality"
              body="Modelled Open-Meteo data derived from CAMS ENSEMBLE, attributed on every air screen. Not a local sensor."
            />
            <Separator />
            <SourceRow
              icon={<ShieldCheck className="size-4" aria-hidden="true" />}
              title="Severity index"
              body="CPCB National AQI (2014) with the maximum sub-index across available pollutants. US and European AQI values are shown separately, never blended."
            />
            <Separator />
            <SourceRow
              icon={<Sparkles className="size-4" aria-hidden="true" />}
              title="Copilot"
              body="Answers come from the server-side Copilot service. The model key stays on the server; no request is made from this browser to the model provider."
            />
            <Separator />
            <SourceRow
              icon={<Info className="size-4" aria-hidden="true" />}
              title="Freshness"
              body="Every air response carries observed and fetched times, an age in minutes and a stale flag from the provider. The interface displays those values; it does not assume a fixed threshold."
            />
            <p className="text-xs text-slate-500">
              Map tiles are © OpenStreetMap contributors. Emission factors are served by the Impact
              factor registry with source and version.
            </p>
          </CardContent>
        </Card>
      </section>

      <section id="local-data" aria-labelledby="local-data-heading" className="scroll-mt-24">
        <Card>
          <CardHeader>
            <CardTitle id="local-data-heading" className="flex items-center gap-2">
              <HardDrive className="size-4 text-brand-700" aria-hidden="true" />
              Local data
            </CardTitle>
            <p className="text-sm text-ink-muted">
              The stores below live in this browser&apos;s localStorage. The family profile and
              recommendation history follow a different model: they are stored on the server under
              an anonymous session token. Manage or delete them on the{" "}
              <Link href="/family" className="font-medium text-brand-800 hover:underline">
                Family intelligence
              </Link>{" "}
              page.
            </p>
          </CardHeader>
          <CardContent className="space-y-1">
            {storedGroups.map((group, index) => (
              <div
                key={group.key}
                className={
                  index === 0
                    ? "flex flex-wrap items-center justify-between gap-3 py-3"
                    : "flex flex-wrap items-center justify-between gap-3 border-t border-line py-3"
                }
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-ink">{group.label}</p>
                  <p className="text-xs text-ink-muted">
                    {group.count} {group.count === 1 ? group.unit : group.plural}
                    {group.detail ? ` · ${group.detail}` : ""}
                  </p>
                </div>
                <ClearButton
                  label={`Clear ${group.label.toLowerCase()}`}
                  disabled={group.count === 0}
                  onClear={() => removeStored(group.key)}
                />
              </div>
            ))}

            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-3">
              <p className="text-sm font-medium text-ink">Reset notification preferences</p>
              <ClearButton
                label="Reset notifications"
                disabled={Object.entries(DEFAULT_NOTIFICATION_PREFERENCES).every(
                  ([key, value]) => preferences[key as keyof NotificationPreferences] === value,
                )}
                onClear={() => removeStored(STORAGE_KEYS.notificationPreferences)}
              />
            </div>
          </CardContent>
        </Card>
      </section>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-line bg-slate-50 px-4 py-3">
        <p className="text-sm text-ink-muted">
          Need the full picture of what this build can and cannot do?
        </p>
        <Link
          href="/#standards"
          className="text-sm font-semibold text-brand-800 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
        >
          Standards and limits
        </Link>
      </div>
    </div>
  );
}

function SourceRow({ icon, title, body }: { icon: ReactNode; title: string; body: string }) {
  return (
    <div className="flex items-start gap-3">
      <span className="mt-0.5 text-brand-700">{icon}</span>
      <div>
        <p className="text-sm font-medium text-ink">{title}</p>
        <p className="mt-0.5 text-xs leading-relaxed text-ink-muted">{body}</p>
      </div>
    </div>
  );
}

function ClearButton({
  label,
  disabled,
  onClear,
}: {
  label: string;
  disabled: boolean;
  onClear: () => void;
}) {
  const [armed, setArmed] = useState(false);

  useEffect(() => {
    if (!armed) {
      return;
    }
    const timer = setTimeout(() => setArmed(false), 5000);
    return () => clearTimeout(timer);
  }, [armed]);

  return (
    <Button
      type="button"
      variant={armed ? "destructive" : "outline"}
      size="sm"
      disabled={disabled}
      onClick={() => {
        if (!armed) {
          setArmed(true);
          return;
        }
        setArmed(false);
        onClear();
      }}
      aria-label={armed ? `${label}: confirm` : label}
    >
      {armed ? "Confirm clear" : "Clear"}
    </Button>
  );
}
