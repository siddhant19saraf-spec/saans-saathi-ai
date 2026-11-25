"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import {
  Accessibility,
  ArrowUpRight,
  BellRing,
  Database,
  HardDrive,
  Info,
  Lock,
  MapPin,
  Settings2,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator, Skeleton } from "@/components/ui/feedback";
import { StatusBadge } from "@/components/ui/status-badge";
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
import { useMotionPreference } from "@/lib/motion";
import { cn } from "@/lib/utils";

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

const SECTIONS = [
  { id: "notifications", label: "Notifications" },
  { id: "data-sources", label: "Data sources" },
  { id: "local-data", label: "Local data" },
  { id: "privacy", label: "Privacy" },
  { id: "preferences", label: "Preferences" },
  { id: "accessibility", label: "Accessibility" },
] as const;

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
  const { reduceMotion, setReduceMotion } = useMotionPreference();

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

  const enabledNotifications = Object.values(preferences).filter(Boolean).length;

  return (
    <div className="space-y-8">
      <nav aria-label="Settings sections">
        <ul className="flex flex-wrap gap-1.5">
          {SECTIONS.map((section) => (
            <li key={section.id}>
              <a
                href={`#${section.id}`}
                className="inline-flex rounded-full border border-line bg-white px-3 py-1.5 text-xs font-medium text-ink-muted transition-colors hover:border-brand-200 hover:text-brand-800 focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
              >
                {section.label}
              </a>
            </li>
          ))}
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
              <div className="flex flex-wrap items-center gap-1.5">
                <Badge variant="neutral">Preferences only</Badge>
                <StatusBadge tone="neutral" icon={false}>
                  {enabledNotifications} of {NOTIFICATION_FIELDS.length} enabled
                </StatusBadge>
              </div>
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
              body="Answers come from the server-side Copilot service. The model key stays on the server; no request is made from this browser to the model provider. Deterministic fallback answers are labelled as such."
            />
            <Separator />
            <SourceRow
              icon={<Info className="size-4" aria-hidden="true" />}
              title="Freshness"
              body="Every air response carries observed and fetched times, an age in minutes and a stale flag from the provider. The interface displays those values; it does not assume a fixed threshold."
            />
            <p className="text-xs text-ink-subtle">
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

      <section id="privacy" aria-labelledby="privacy-heading" className="scroll-mt-24">
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle id="privacy-heading" className="flex items-center gap-2">
                <Lock className="size-4 text-brand-700" aria-hidden="true" />
                Privacy
              </CardTitle>
              <StatusBadge tone="positive">No account required</StatusBadge>
            </div>
            <p className="text-sm text-ink-muted">
              What this build stores, where it lives and how to remove it. There is no advertising,
              analytics or third-party tracking script in this build.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <SourceRow
              icon={<Lock className="size-4" aria-hidden="true" />}
              title="Anonymous family session"
              body="Family Intelligence creates a random session token stored in this browser. The backend keeps only a hash of the token. No name, email address or password is required, and there is no account recovery."
            />
            <Separator />
            <SourceRow
              icon={<ShieldCheck className="size-4" aria-hidden="true" />}
              title="Health flags are optional"
              body="Age bands and coarse health flags are only stored after explicit consent. Withdraw consent or delete the household from Family Intelligence at any time. Guidance is general and never medical advice."
            />
            <Separator />
            <SourceRow
              icon={<HardDrive className="size-4" aria-hidden="true" />}
              title="Local-first stores"
              body="Locations, routine activities, impact entries, indoor checks and preferences stay in this browser unless a page explicitly calls the backend. Clearing a store above removes it immediately."
            />
            <Separator />
            <SourceRow
              icon={<MapPin className="size-4" aria-hidden="true" />}
              title="Coordinates"
              body="Coordinates are rounded to two decimal places before they are sent to the backend. A map point is a coordinate, not a monitoring station, and no precise device location is stored unless you add it."
            />
          </CardContent>
        </Card>
      </section>

      <section id="preferences" aria-labelledby="preferences-heading" className="scroll-mt-24">
        <Card>
          <CardHeader>
            <CardTitle id="preferences-heading" className="flex items-center gap-2">
              <Settings2 className="size-4 text-brand-700" aria-hidden="true" />
              Preferences
            </CardTitle>
            <p className="text-sm text-ink-muted">
              Where the other preference surfaces live. Each one saves independently in this
              browser or, for the household profile, under the anonymous session.
            </p>
          </CardHeader>
          <CardContent className="space-y-1">
            <PreferenceRow
              title="Alert delivery"
              description={`${enabledNotifications} of ${NOTIFICATION_FIELDS.length} enabled · saved in this browser`}
              href="#notifications"
              action="Review notifications"
            />
            <PreferenceRow
              title="Travel and commute"
              description={
                ecoPreferences.modes.length > 0
                  ? `${ecoPreferences.modes.length} modes selected · usual trip ${ecoPreferences.usualDistanceKm} km`
                  : "No travel modes selected yet"
              }
              href="/eco-route"
              action="Open EcoRoute"
            />
            <PreferenceRow
              title="Household activity preferences"
              description="Activity windows, flexibility and transport preferences are stored with the family profile."
              href="/family"
              action="Open Family intelligence"
            />
            <PreferenceRow
              title="Language and locale"
              description="English (India) is the only interface locale in this build. Numbers and dates use en-IN formatting."
            />
          </CardContent>
        </Card>
      </section>

      <section id="accessibility" aria-labelledby="accessibility-heading" className="scroll-mt-24">
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle id="accessibility-heading" className="flex items-center gap-2">
                <Accessibility className="size-4 text-brand-700" aria-hidden="true" />
                Accessibility
              </CardTitle>
              <StatusBadge tone="neutral" icon={false}>
                WCAG 2.2 AA target
              </StatusBadge>
            </div>
            <p className="text-sm text-ink-muted">
              Controls below apply immediately. Your operating system&apos;s reduced-motion setting
              is also respected automatically.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start justify-between gap-4 rounded-xl border border-line bg-surface-muted/60 px-3.5 py-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-ink" id="reduce-motion-label">
                  Reduce motion
                </p>
                <p className="mt-0.5 text-xs text-ink-muted" id="reduce-motion-description">
                  Turns off decorative fades and slides across the app, including chart and card
                  transitions. System-level reduced motion is always honoured.
                </p>
              </div>
              <Switch
                checked={reduceMotion}
                onCheckedChange={setReduceMotion}
                aria-labelledby="reduce-motion-label"
                aria-describedby="reduce-motion-description"
                className="mt-1"
              />
            </div>

            <dl className="grid gap-3 sm:grid-cols-2">
              <AccessibilityFact
                title="Keyboard"
                body="Every route is reachable from the sidebar and the mobile drawer. A skip link jumps to the main content, and dialogs trap focus."
              />
              <AccessibilityFact
                title="Focus visibility"
                body="Interactive elements use a consistent visible focus ring. Focus is never removed without a replacement."
              />
              <AccessibilityFact
                title="Colour is never the only signal"
                body="AQI categories pair colour with a label, an icon and a range. Charts include text summaries and table-style values."
              />
              <AccessibilityFact
                title="Motion and zoom"
                body="Layouts reflow from 320px upward, text remains readable at 200% zoom, and decorative animation is suppressed under reduced motion."
              />
            </dl>

            <p className="text-xs leading-relaxed text-ink-subtle">
              Known limits: automated checks and Chromium-based browsers are used in this build. A
              screen-reader and physical-device audit is still recommended before production use.
            </p>
          </CardContent>
        </Card>
      </section>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-line bg-white px-4 py-3">
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

function PreferenceRow({
  title,
  description,
  href,
  action,
}: {
  title: string;
  description: string;
  href?: string;
  action?: string;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line py-3 last:border-0">
      <div className="min-w-0">
        <p className="text-sm font-medium text-ink">{title}</p>
        <p className="mt-0.5 text-xs text-ink-muted">{description}</p>
      </div>
      {href && action ? (
        <Link
          href={href}
          className="inline-flex items-center gap-1 text-xs font-semibold text-brand-700 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
        >
          {action}
          <ArrowUpRight className="size-3.5" aria-hidden="true" />
        </Link>
      ) : null}
    </div>
  );
}

function AccessibilityFact({ title, body }: { title: string; body: string }) {
  return (
    <div className={cn("rounded-xl border border-line bg-white px-3 py-2.5")}>
      <dt className="text-xs font-semibold text-ink">{title}</dt>
      <dd className="mt-0.5 text-xs leading-relaxed text-ink-muted">{body}</dd>
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
