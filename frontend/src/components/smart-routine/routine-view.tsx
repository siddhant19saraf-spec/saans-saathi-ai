"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { CalendarClock, Plus, Sparkles, Trash2 } from "lucide-react";
import { useForm } from "react-hook-form";

import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FieldError, Input, Label, Select } from "@/components/ui/field";
import { Skeleton } from "@/components/ui/feedback";
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

function endTime(start: string, durationMin: number): string {
  const parts = start.split(":");
  const hours = Number(parts[0] ?? 0);
  const minutes = Number(parts[1] ?? 0);
  const total = hours * 60 + minutes + durationMin;
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

export function RoutineView() {
  const { activities, add, remove, hydrated } = useRoutineActivities();
  const { profile: household } = useFamilyOverview();

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

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Add an activity</CardTitle>
            <p className="text-sm text-ink-muted">
              Saved locally. Up to 12 activities; adding more replaces the oldest.
            </p>
          </CardHeader>
          <CardContent>
            <form
              noValidate
              onSubmit={handleSubmit((values) => {
                add(toRoutineActivity(values));
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
                      errors.durationMin ? "activity-duration-error" : "activity-duration-hint"
                    }
                    {...register("durationMin", { valueAsNumber: true })}
                  />
                  <FieldError id="activity-duration-error">
                    {errors.durationMin?.message}
                  </FieldError>
                </div>
              </div>
              <p id="activity-duration-hint" className="text-xs text-slate-500">
                15–180 minutes per activity.
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

              <Button type="submit" className="w-full">
                <Plus className="size-4" aria-hidden="true" />
                Add to routine
              </Button>
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
            air-quality data and a household profile. This planner stores your activities and never
            invents a recommendation.
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
            <Badge variant="neutral">{activities.length} of 12 activities</Badge>
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
                      className="text-[11px] font-semibold tracking-[0.12em] text-slate-500 uppercase"
                    >
                      {group}
                    </h3>
                    <ul className="mt-2 flex flex-col gap-2">
                      {groupActivities.map((activity) => (
                        <RoutineItem
                          key={activity.id}
                          activity={activity}
                          onRemove={() => remove(activity.id)}
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
  );
}

function RoutineItem({ activity, onRemove }: { activity: RoutineActivity; onRemove: () => void }) {
  return (
    <li className="flex items-start gap-3 rounded-xl border border-line bg-white px-3 py-3">
      <div className="w-24 shrink-0">
        <p className="text-sm font-semibold text-ink">{activity.start}</p>
        <p className="text-[11px] text-slate-500">
          to {endTime(activity.start, activity.durationMin)}
        </p>
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
        </div>
      </div>
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Remove ${activity.title}`}
        className="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-700 focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:outline-none"
      >
        <Trash2 className="size-4" aria-hidden="true" />
      </button>
    </li>
  );
}
