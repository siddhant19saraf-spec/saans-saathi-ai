"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Trash2 } from "lucide-react";
import { Controller, useFieldArray, useForm, type Control } from "react-hook-form";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { FieldError, Input, Label, Select } from "@/components/ui/field";
import { Switch } from "@/components/ui/switch";
import {
  ACTIVITY_OPTIONS,
  TRANSPORT_LABELS,
  WEEKDAY_OPTIONS,
  newWindow,
  preferencesFormSchema,
  preferencesToForm,
  toPreferencesInput,
  type FamilyPreferencesResponse,
  type PreferencesFormValues,
  type PreferencesInput,
} from "@/features/family/schema";

export function PreferencesForm({
  initial,
  busy,
  onSave,
}: {
  initial: FamilyPreferencesResponse;
  busy: boolean;
  onSave: (input: PreferencesInput) => Promise<boolean>;
}) {
  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PreferencesFormValues>({
    resolver: zodResolver(preferencesFormSchema),
    defaultValues: preferencesToForm(initial),
  });

  const { fields, append, remove } = useFieldArray({ control, name: "activity_windows" });
  const listError = errors.activity_windows?.root?.message ?? errors.activity_windows?.message;

  return (
    <form
      noValidate
      onSubmit={handleSubmit(async (values) => {
        await onSave(toPreferencesInput(values));
      })}
      className="space-y-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="max-w-xl text-sm leading-relaxed text-ink-muted">
          Each activity window is evaluated with your household timezone, current pollution data and
          the deterministic rules engine. Suggested times come from the 48-hour PM2.5 forecast.
        </p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => append(newWindow("evening_exercise"))}
          disabled={fields.length >= 12}
        >
          <Plus className="size-3.5" aria-hidden="true" />
          Add activity
        </Button>
      </div>

      {listError ? (
        <Alert variant="error">
          <AlertDescription>{listError}</AlertDescription>
        </Alert>
      ) : null}

      {fields.length === 0 ? (
        <Alert variant="warning">
          <AlertDescription>
            No activities yet. Recommendations need at least one activity window; generation will
            return no recommendations until one is added.
          </AlertDescription>
        </Alert>
      ) : null}

      <div className="space-y-4">
        {fields.map((field, index) => {
          const windowErrors = errors.activity_windows?.[index];
          return (
            <fieldset key={field.id} className="rounded-xl border border-line bg-slate-50/50 p-4">
              <div className="flex items-center justify-between gap-2">
                <legend className="text-sm font-semibold text-ink">Activity {index + 1}</legend>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="text-red-700 hover:bg-red-50 hover:text-red-800"
                  onClick={() => remove(index)}
                  aria-label={`Remove activity ${index + 1}`}
                >
                  <Trash2 className="size-3.5" aria-hidden="true" />
                  Remove
                </Button>
              </div>

              <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`window-${index}-activity`}>Activity</Label>
                  <Select
                    id={`window-${index}-activity`}
                    aria-invalid={windowErrors?.activity ? true : undefined}
                    {...register(`activity_windows.${index}.activity`)}
                  >
                    {ACTIVITY_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </Select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`window-${index}-title`}>Label</Label>
                  <Input
                    id={`window-${index}-title`}
                    aria-invalid={windowErrors?.title ? true : undefined}
                    {...register(`activity_windows.${index}.title`)}
                  />
                  <FieldError id={`window-${index}-title-error`}>
                    {windowErrors?.title?.message}
                  </FieldError>
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`window-${index}-start`}>Preferred start</Label>
                  <Input
                    id={`window-${index}-start`}
                    type="time"
                    aria-invalid={windowErrors?.start ? true : undefined}
                    {...register(`activity_windows.${index}.start`)}
                  />
                  <FieldError id={`window-${index}-start-error`}>
                    {windowErrors?.start?.message}
                  </FieldError>
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`window-${index}-duration`}>Duration, minutes</Label>
                  <Input
                    id={`window-${index}-duration`}
                    type="number"
                    min={15}
                    max={180}
                    step={5}
                    aria-invalid={windowErrors?.duration_min ? true : undefined}
                    {...register(`activity_windows.${index}.duration_min`, {
                      valueAsNumber: true,
                    })}
                  />
                  <FieldError id={`window-${index}-duration-error`}>
                    {windowErrors?.duration_min?.message}
                  </FieldError>
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`window-${index}-flexibility`}>Flexibility, minutes</Label>
                  <Input
                    id={`window-${index}-flexibility`}
                    type="number"
                    min={0}
                    max={180}
                    step={15}
                    aria-invalid={windowErrors?.flexibility_min ? true : undefined}
                    {...register(`activity_windows.${index}.flexibility_min`, {
                      valueAsNumber: true,
                    })}
                  />
                  <FieldError id={`window-${index}-flexibility-error`}>
                    {windowErrors?.flexibility_min?.message}
                  </FieldError>
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`window-${index}-intensity`}>Intensity</Label>
                  <Select
                    id={`window-${index}-intensity`}
                    {...register(`activity_windows.${index}.intensity`)}
                  >
                    <option value="light">Light</option>
                    <option value="moderate">Moderate</option>
                    <option value="vigorous">Vigorous</option>
                  </Select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`window-${index}-venue`}>Venue</Label>
                  <Select
                    id={`window-${index}-venue`}
                    {...register(`activity_windows.${index}.venue`)}
                  >
                    <option value="outdoor">Outdoor</option>
                    <option value="indoor">Indoor</option>
                  </Select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`window-${index}-transport`}>Transport</Label>
                  <Select
                    id={`window-${index}-transport`}
                    {...register(`activity_windows.${index}.transport_mode`)}
                  >
                    <option value="">Use household preference</option>
                    <option value="walk">Walking</option>
                    <option value="cycle">Cycling</option>
                    <option value="public">Public transport</option>
                    <option value="private">Private vehicle</option>
                    <option value="mixed">Mixed</option>
                  </Select>
                </div>

                <div className="flex flex-col gap-1.5 sm:col-span-2 lg:col-span-3">
                  <Label htmlFor={`window-${index}-alternative`}>
                    Indoor alternative{" "}
                    <span className="font-normal text-slate-500">
                      (optional; the rules engine supplies a default when empty)
                    </span>
                  </Label>
                  <Input
                    id={`window-${index}-alternative`}
                    placeholder="e.g. Indoor stretching in a closed room"
                    {...register(`activity_windows.${index}.indoor_alternative`)}
                  />
                  <FieldError id={`window-${index}-alternative-error`}>
                    {windowErrors?.indoor_alternative?.message}
                  </FieldError>
                </div>
              </div>

              <Controller
                control={control}
                name={`activity_windows.${index}.days`}
                render={({ field: daysField }) => (
                  <fieldset className="mt-3 flex flex-wrap gap-3">
                    <legend className="w-full text-sm font-medium text-ink">Days</legend>
                    {WEEKDAY_OPTIONS.map((day) => {
                      const checked = daysField.value.includes(day.value);
                      const inputId = `window-${index}-day-${day.value}`;
                      return (
                        <div key={day.value} className="flex items-center gap-1.5">
                          <Checkbox
                            id={inputId}
                            checked={checked}
                            onCheckedChange={(next) =>
                              daysField.onChange(
                                next === true
                                  ? [...daysField.value, day.value]
                                  : daysField.value.filter((value) => value !== day.value),
                              )
                            }
                            className="size-4"
                          />
                          <label
                            htmlFor={inputId}
                            className="cursor-pointer text-xs text-ink-muted"
                          >
                            {day.label}
                          </label>
                        </div>
                      );
                    })}
                    <FieldError id={`window-${index}-days-error`}>
                      {windowErrors?.days?.message}
                    </FieldError>
                  </fieldset>
                )}
              />
            </fieldset>
          );
        })}
      </div>

      <fieldset className="rounded-xl border border-line bg-white p-4">
        <legend className="px-1 text-sm font-semibold text-ink">Household defaults</legend>
        <div className="mt-3 grid gap-4 sm:grid-cols-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="preferences-transport">Transport preference</Label>
            <Select id="preferences-transport" {...register("transport_mode")}>
              {Object.entries(TRANSPORT_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="preferences-threshold">Alert threshold (AQI)</Label>
            <Input
              id="preferences-threshold"
              type="number"
              min={0}
              max={500}
              step={10}
              {...register("alert_threshold_aqi", { valueAsNumber: true })}
            />
            <FieldError id="threshold-error">{errors.alert_threshold_aqi?.message}</FieldError>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="preferences-quiet-start">
              Quiet hours start <span className="font-normal text-slate-500">(optional)</span>
            </Label>
            <Input id="preferences-quiet-start" type="time" {...register("quiet_hours_start")} />
            <FieldError id="quiet-start-error">{errors.quiet_hours_start?.message}</FieldError>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="preferences-quiet-end">
              Quiet hours end <span className="font-normal text-slate-500">(optional)</span>
            </Label>
            <Input id="preferences-quiet-end" type="time" {...register("quiet_hours_end")} />
            <FieldError id="quiet-end-error">{errors.quiet_hours_end?.message}</FieldError>
          </div>
        </div>

        <div className="mt-4 space-y-3 border-t border-line pt-4">
          <NotificationToggle
            control={control}
            name="notifications_enabled"
            id="preferences-notifications"
            label="Notification preferences enabled"
            description="Stored with the profile; no delivery channel is connected in this build."
          />
          <NotificationToggle
            control={control}
            name="notify_alerts"
            id="preferences-alerts"
            label="Air-quality alerts"
            description="Preference for alerts when the CPCB category is poor or worse."
          />
          <NotificationToggle
            control={control}
            name="notify_daily_summary"
            id="preferences-summary"
            label="Daily summary"
            description="Preference for a daily summary of recommendations."
          />
        </div>
      </fieldset>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-md text-xs leading-relaxed text-slate-500">
          Preferences are stored on the server. The rules engine, not the AI model, decides every
          action.
        </p>
        <Button type="submit" disabled={busy || isSubmitting}>
          {busy ? "Saving…" : "Save preferences"}
        </Button>
      </div>
    </form>
  );
}

function NotificationToggle({
  control,
  name,
  id,
  label,
  description,
}: {
  control: Control<PreferencesFormValues>;
  name: "notifications_enabled" | "notify_alerts" | "notify_daily_summary";
  id: string;
  label: string;
  description: string;
}) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field }) => (
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <label htmlFor={id} className="text-sm font-medium text-ink">
              {label}
            </label>
            <p className="mt-0.5 text-xs text-ink-muted">{description}</p>
          </div>
          <Switch
            id={id}
            checked={field.value}
            onCheckedChange={(checked) => field.onChange(checked)}
            className="mt-1"
          />
        </div>
      )}
    />
  );
}
