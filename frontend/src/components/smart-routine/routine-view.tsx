"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  CalendarClock,
  CircleAlert,
  Pencil,
  Plus,
  Sparkles,
  Timer,
  Trash2,
  X,
} from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { EmptyState } from "@/components/shared/empty-state";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FieldError, Input, Label, Select } from "@/components/ui/field";
import { Skeleton } from "@/components/ui/feedback";
import { StatusBadge } from "@/components/ui/status-badge";
import { useFamilyOverview } from "@/features/family/use-family";
import {
  INTENSITIES,
  VENUES,
  routineActivityFormSchema,
  sortByStart,
  toRoutineActivity,
  type RoutineActivity,
  type RoutineActivityFormValues,
} from "@/features/routine/schema";
import { useRoutineActivities } from "@/features/routine/use-routine";
import { cn } from "@/lib/utils";

function minutesOf(time: string): number {
  const parts = time.split(":");
  return Number(parts[0] ?? 0) * 60 + Number(parts[1] ?? 0);
}

function endMinutes(activity: RoutineActivity): number {
  return minutesOf(activity.start) + activity.durationMin;
}

function endTime(start: string, durationMin: number): string {
  const total = minutesOf(start) + durationMin;
  const endHours = Math.floor((total % (24 * 60)) / 60);
  const endMinutes = total % 60;
  return `${String(endHours).padStart(2, "0")}:${String(endMinutes).padStart(2, "0")}`;
}

function groupFor(start: string): string {
  const hour = Number(start.split(":")[0] ?? 0);
  if (hour < 12) return "Morning";
  if (hour < 17) return "Afternoon";
  return "Evening";
}

function overlaps(a: RoutineActivity, b: RoutineActivity): boolean {
  const aStart = minutesOf(a.start);
  const aEnd = endMinutes(a);
  const bStart = minutesOf(b.start);
  const bEnd = endMinutes(b);
  if (aStart < bEnd && bStart < aEnd) return true;
  // A plan that runs past midnight overlaps an early-morning plan.
  return aEnd > 24 * 60 && bStart + 24 * 60 < aEnd;
}

function findConflicts(activities: RoutineActivity[]): [RoutineActivity, RoutineActivity][] {
  const ordered = sortByStart(activities);
  const pairs: [RoutineActivity, RoutineActivity][] = [];
  for (let i = 0; i < ordered.length; i += 1) {
    for (let j = i + 1; j < ordered.length; j += 1) {
      const first = ordered[i];
      const second = ordered[j];
      if (first && second && overlaps(first, second)) pairs.push([first, second]);
    }
  }
  return pairs;
}

export function RoutineView() {
  const { activities, add, remove, update, hydrated } = useRoutineActivities();
  const { profile: household } = useFamilyOverview();
  const [editingId, setEditingId] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<RoutineActivityFormValues>({
    resolver: zodResolver(routineActivityFormSchema),
    defaultValues: {
      title: "",
      start: "07:00",
      durationMin: 30,
      venue: "outdoor",
      intensity: "moderate",
    },
  });

  if (!hydrated) {
    return (
      <div aria-busy="true" aria-live="polite" className="space-y-4">
        <span className="sr-only">Loading routine planner</span>
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  const ordered = sortByStart(activities);
  const groups = ["Morning", "Afternoon", "Evening"] as const;
  const conflicts = findConflicts(activities);
  const totalMinutes = activities.reduce((sum, activity) => sum + activity.durationMin, 0);
  const outdoorMinutes = activities
    .filter((activity) => activity.venue === "outdoor")
    .reduce((sum, activity) => sum + activity.durationMin, 0);
  const timezoneLabel = household?.timezone ? ` (${household.timezone})` : "";

  function beginEdit(activity: RoutineActivity) {
    setEditingId(activity.id);
    reset({
      title: activity.title,
      start: activity.start,
      durationMin: activity.durationMin,
      venue: activity.venue,
      intensity: activity.intensity,
    });
    document.getElementById("routine-form")?.scrollIntoView({ block: "start" });
    document.getElementById("activity-title")?.focus();
  }

  function cancelEdit() {
    setEditingId(null);
    reset({
      title: "",
      start: "07:00",
      durationMin: 30,
      venue: "outdoor",
      intensity: "moderate",
    });
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-line bg-white px-4 py-3">
          <p className="text-[11px] font-semibold tracking-wide text-ink-subtle uppercase">
            Planned activities
          </p>
          <p className="metric-value mt-1 text-2xl font-semibold text-ink">
            {activities.length}
            <span className="ml-1 text-xs font-medium text-ink-muted">of 12</span>
          </p>
        </div>
        <div className="rounded-xl border border-line bg-white px-4 py-3">
          <p className="text-[11px] font-semibold tracking-wide text-ink-subtle uppercase">
            Total planned time
          </p>
          <p className="metric-value mt-1 text-2xl font-semibold text-ink">
            {Math.floor(totalMinutes / 60)}h {totalMinutes % 60}m
          </p>
        </div>
        <div className="rounded-xl border border-line bg-white px-4 py-3">
          <p className="text-[11px] font-semibold tracking-wide text-ink-subtle uppercase">
            Outdoors
          </p>
          <p className="metric-value mt-1 text-2xl font-semibold text-ink">
            {outdoorMinutes}
            <span className="ml-1 text-xs font-medium text-ink-muted">min</span>
          </p>
        </div>
      </div>

      {conflicts.length > 0 ? (
        <Alert variant="warning">
          <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <AlertDescription>
            <p className="font-semibold">
              {conflicts.length} overlapping {conflicts.length === 1 ? "pair" : "pairs"} in this plan
            </p>
            <ul className="mt-1.5 space-y-0.5">
              {conflicts.map(([first, second]) => (
                <li key={`${first.id}-${second.id}`}>
                  {first.title} ({first.start}–{endTime(first.start, first.durationMin)}) overlaps{" "}
                  {second.title} ({second.start}–{endTime(second.start, second.durationMin)}).
                </li>
              ))}
            </ul>
            <p className="mt-1.5 text-xs">
              This is a schedule check only. It does not judge whether either time is safe.
            </p>
          </AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
        <div className="space-y-4">
          <Card id="routine-form" className="scroll-mt-24">
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <CardTitle>{editingId ? "Edit activity" : "Add an activity"}</CardTitle>
                  <p className="mt-1 text-sm text-ink-muted">
                    Saved locally. Up to 12 activities; adding more replaces the oldest.
                  </p>
                </div>
                {editingId ? (
                  <button
                    type="button"
                    onClick={cancelEdit}
                    aria-label="Cancel editing"
                    className="rounded-md p-1 text-ink-subtle hover:bg-surface-muted hover:text-ink focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
                  >
                    <X className="size-4" aria-hidden="true" />
                  </button>
                ) : null}
              </div>
            </CardHeader>
            <CardContent>
              <form
                noValidate
                onSubmit={handleSubmit((values) => {
                  const next = toRoutineActivity(values);
                  if (editingId) {
                    update(editingId, next);
                    cancelEdit();
                    return;
                  }
                  add(next);
                  reset({
                    title: "",
                    start: values.start,
                    durationMin: 30,
                    venue: values.venue,
                    intensity: values.intensity,
                  });
                })}
                className="space-y-4"
              >
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="activity-title">Activity</Label>
                  <Input
                    id="activity-title"
                    placeholder="e.g. Morning walk"
                    autoComplete="off"
                    aria-invalid={errors.title ? true : undefined}
                    aria-describedby={errors.title ? "activity-title-error" : undefined}
                    {...register("title")}
                  />
                  <FieldError id="activity-title-error">{errors.title?.message}</FieldError>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="activity-start">Start time</Label>
                    <Input
                      id="activity-start"
                      type="time"
                      aria-invalid={errors.start ? true : undefined}
                      aria-describedby={errors.start ? "activity-start-error" : undefined}
                      {...register("start")}
                    />
                    <FieldError id="activity-start-error">{errors.start?.message}</FieldError>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="activity-duration">Minutes</Label>
                    <Input
                      id="activity-duration"
                      type="number"
                      min={15}
                      max={180}
                      step={5}
                      aria-invalid={errors.durationMin ? true : undefined}
                      aria-describedby={
                        errors.durationMin
                          ? "activity-duration-error"
                          : "activity-duration-hint"
                      }
                      {...register("durationMin", { valueAsNumber: true })}
                    />
                    <FieldError id="activity-duration-error">
                      {errors.durationMin?.message}
                    </FieldError>
                  </div>
                </div>
                <p id="activity-duration-hint" className="text-xs text-ink-subtle">
                  15–180 minutes per activity. Times are wall-clock times in your household
                  timezone{timezoneLabel}.
                </p>

                <div className="grid grid-cols-2 gap-3">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="activity-venue">Where</Label>
                    <Select id="activity-venue" {...register("venue")}>
                      {VENUES.map((venue) => (
                        <option key={venue.value} value={venue.value}>
                          {venue.label}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="activity-intensity">Intensity</Label>
                    <Select id="activity-intensity" {...register("intensity")}>
                      {INTENSITIES.map((intensity) => (
                        <option key={intensity.value} value={intensity.value}>
                          {intensity.label}
                        </option>
                      ))}
                    </Select>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button type="submit" className="flex-1">
                    {editingId ? (
                      <>
                        <Pencil className="size-4" aria-hidden="true" />
                        Save changes
                      </>
                    ) : (
                      <>
                        <Plus className="size-4" aria-hidden="true" />
                        Add to routine
                      </>
                    )}
                  </Button>
                  {editingId ? (
                    <Button type="button" variant="outline" onClick={cancelEdit}>
                      Cancel
                    </Button>
                  ) : null}
                </div>
              </form>
            </CardContent>
          </Card>

          <div className="rounded-2xl border border-brand-100 bg-brand-50/70 p-4">
            <p className="flex items-center gap-2 text-sm font-semibold text-brand-900">
              <Sparkles className="size-4" aria-hidden="true" />
              Timing guidance is not connected
            </p>
            <p className="mt-1.5 text-xs leading-relaxed text-brand-900/80">
              Exposure-aware scheduling is produced by the SmartRoutine service, which needs current
              air-quality data and a household profile. This planner stores your activities and
              never invents a recommendation.
            </p>
            <div className="mt-2 flex flex-wrap gap-3">
              <Link
                href="/dashboard"
                className="text-xs font-semibold text-brand-800 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
              >
                Check current air
              </Link>
              <Link
                href="/family"
                className="text-xs font-semibold text-brand-800 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
              >
                {household ? "Review household" : "Create household profile"}
              </Link>
            </div>
          </div>
        </div>

        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle className="flex items-center gap-2">
                <CalendarClock className="size-4 text-brand-700" aria-hidden="true" />
                Your day
              </CardTitle>
              <div className="flex flex-wrap items-center gap-1.5">
                <StatusBadge tone="neutral" icon={false}>
                  <Timer className="size-3.5" aria-hidden="true" />
                  {totalMinutes} planned min
                </StatusBadge>
                <Badge variant="neutral">{activities.length} of 12 activities</Badge>
              </div>
            </div>
            <p className="text-sm text-ink-muted">
              Ordered by start time. This is a saved plan, not an exposure ranking.
            </p>
          </CardHeader>
          <CardContent>
            {ordered.length === 0 ? (
              <EmptyState
                icon={CalendarClock}
                title="No activities yet"
                description="Add a walk, commute or indoor routine using the form. Activities are saved in this browser."
                className="border-0 bg-transparent py-8"
              />
            ) : (
              <div className="space-y-5">
                {groups.map((group) => {
                  const groupActivities = ordered.filter(
                    (activity) => groupFor(activity.start) === group,
                  );
                  if (groupActivities.length === 0) {
                    return null;
                  }
                  return (
                    <section key={group} aria-labelledby={`group-${group}`}>
                      <h3
                        id={`group-${group}`}
                        className="text-[11px] font-semibold tracking-[0.12em] text-ink-subtle uppercase"
                      >
                        {group}
                      </h3>
                      <ul className="mt-2 flex flex-col gap-2">
                        {groupActivities.map((activity) => (
                          <RoutineItem
                            key={activity.id}
                            activity={activity}
                            conflicting={conflicts.some(
                              (pair) => pair[0].id === activity.id || pair[1].id === activity.id,
                            )}
                            onEdit={() => beginEdit(activity)}
                            onRemove={() => {
                              if (editingId === activity.id) cancelEdit();
                              remove(activity.id);
                            }}
                          />
                        ))}
                      </ul>
                    </section>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function RoutineItem({
  activity,
  conflicting,
  onEdit,
  onRemove,
}: {
  activity: RoutineActivity;
  conflicting: boolean;
  onEdit: () => void;
  onRemove: () => void;
}) {
  return (
    <li
      className={cn(
        "flex items-start gap-3 rounded-xl border bg-white px-3 py-3",
        conflicting ? "border-amber-300" : "border-line",
      )}
    >
      <div className="flex w-20 shrink-0 flex-col items-start sm:w-24">
        <p className="metric-value text-sm font-semibold text-ink">{activity.start}</p>
        <p className="text-[11px] text-ink-subtle">to {endTime(activity.start, activity.durationMin)}</p>
        <span
          aria-hidden="true"
          className={cn(
            "mt-2 h-1 w-10 rounded-full",
            activity.venue === "outdoor" ? "bg-brand-500" : "bg-sky-400",
          )}
        />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-ink">{activity.title}</p>
        <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[11px] text-ink-muted">
          <Badge variant="outline" className="px-1.5 py-0 text-[10px]">
            {VENUES.find((venue) => venue.value === activity.venue)?.label ?? activity.venue}
          </Badge>
          <Badge variant="neutral" className="px-1.5 py-0 text-[10px]">
            {INTENSITIES.find((intensity) => intensity.value === activity.intensity)?.label ??
              activity.intensity}
          </Badge>
          <span>{activity.durationMin} min</span>
          {conflicting ? (
            <span className="font-medium text-amber-800">Overlaps another activity</span>
          ) : null}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-0.5">
        <button
          type="button"
          onClick={onEdit}
          aria-label={`Edit ${activity.title}`}
          className="rounded-md p-1.5 text-ink-subtle transition-colors hover:bg-surface-muted hover:text-ink focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
        >
          <Pencil className="size-4" aria-hidden="true" />
        </button>
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove ${activity.title}`}
          className="rounded-md p-1.5 text-ink-subtle transition-colors hover:bg-red-50 hover:text-red-700 focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:outline-none"
        >
          <Trash2 className="size-4" aria-hidden="true" />
        </button>
      </div>
    </li>
  );
}
