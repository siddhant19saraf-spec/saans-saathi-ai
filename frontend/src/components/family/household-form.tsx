"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { LocateFixed, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Controller, useFieldArray, useForm, useWatch } from "react-hook-form";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { FieldError, Input, Label, Select } from "@/components/ui/field";
import {
  AGE_BAND_OPTIONS,
  COOKING_FUEL_OPTIONS,
  DWELLING_OPTIONS,
  HEALTH_FLAG_OPTIONS,
  emptyProfileForm,
  profileFormSchema,
  profileToForm,
  toProfileInput,
  type FamilyProfile,
  type ProfileFormValues,
  type ProfileInput,
} from "@/features/family/schema";

const TIMEZONE_OPTIONS = [
  "Asia/Kolkata",
  "Asia/Karachi",
  "Asia/Dhaka",
  "Asia/Kathmandu",
  "Asia/Colombo",
  "Asia/Dubai",
  "UTC",
];

export function HouseholdForm({
  initial,
  healthConsent,
  busy,
  onSave,
}: {
  initial: FamilyProfile | null;
  healthConsent: boolean;
  busy: boolean;
  onSave: (input: ProfileInput, options: { grantHealthConsent: boolean }) => Promise<boolean>;
}) {
  const {
    register,
    control,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileFormSchema),
    defaultValues: initial
      ? profileToForm(initial, healthConsent)
      : { ...emptyProfileForm(), health_consent: healthConsent },
  });

  const hasPurifier = useWatch({ control, name: "has_purifier" });

  const { fields, append, remove } = useFieldArray({ control, name: "members" });
  const [locationError, setLocationError] = useState<string | null>(null);
  const memberListError = errors.members?.root?.message ?? errors.members?.message;
  const timezones =
    initial && !TIMEZONE_OPTIONS.includes(initial.timezone)
      ? [initial.timezone, ...TIMEZONE_OPTIONS]
      : TIMEZONE_OPTIONS;

  function useCurrentLocation() {
    setLocationError(null);
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setLocationError("This browser does not provide a location.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setValue("lat", position.coords.latitude.toFixed(5), { shouldValidate: true });
        setValue("lon", position.coords.longitude.toFixed(5), { shouldValidate: true });
      },
      () => setLocationError("Location access was denied. Enter coordinates manually."),
      { timeout: 10_000 },
    );
  }

  return (
    <form
      noValidate
      onSubmit={handleSubmit(async (values) => {
        await onSave(toProfileInput(values), {
          grantHealthConsent: values.health_consent && !healthConsent,
        });
      })}
      className="space-y-6"
    >
      <div className="rounded-2xl border border-line bg-white p-5 shadow-card">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="household-name">Household name</Label>
          <Input
            id="household-name"
            placeholder="e.g. Sharma household"
            aria-invalid={errors.name ? true : undefined}
            aria-describedby={errors.name ? "household-name-error" : undefined}
            {...register("name")}
          />
          <FieldError id="household-name-error">{errors.name?.message}</FieldError>
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="household-city">
              City <span className="font-normal text-slate-500">(optional)</span>
            </Label>
            <Input id="household-city" placeholder="e.g. New Delhi" {...register("city")} />
            <FieldError id="city-error">{errors.city?.message}</FieldError>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="household-timezone">Timezone</Label>
            <Select id="household-timezone" {...register("timezone")}>
              {timezones.map((timezone) => (
                <option key={timezone} value={timezone}>
                  {timezone}
                </option>
              ))}
            </Select>
            <FieldError id="timezone-error">{errors.timezone?.message}</FieldError>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="household-lat">Latitude</Label>
            <Input
              id="household-lat"
              inputMode="decimal"
              placeholder="28.6139"
              aria-invalid={errors.lat ? true : undefined}
              aria-describedby={errors.lat ? "lat-error" : undefined}
              {...register("lat")}
            />
            <FieldError id="lat-error">{errors.lat?.message}</FieldError>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="household-lon">Longitude</Label>
            <Input
              id="household-lon"
              inputMode="decimal"
              placeholder="77.2090"
              aria-invalid={errors.lon ? true : undefined}
              aria-describedby={errors.lon ? "lon-error" : undefined}
              {...register("lon")}
            />
            <FieldError id="lon-error">{errors.lon?.message}</FieldError>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-3">
          <Button type="button" variant="outline" size="sm" onClick={useCurrentLocation}>
            <LocateFixed className="size-3.5" aria-hidden="true" />
            Use my current location
          </Button>
          <p className="text-xs text-slate-500">
            Coordinates are used only to request air quality for this location.
          </p>
        </div>
        {locationError ? (
          <p role="alert" className="mt-2 text-xs font-medium text-red-700">
            {locationError}
          </p>
        ) : null}

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="household-dwelling">Dwelling</Label>
            <Select id="household-dwelling" {...register("dwelling")}>
              {DWELLING_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="household-fuel">Cooking fuel</Label>
            <Select id="household-fuel" {...register("cooking_fuel")}>
              {COOKING_FUEL_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="household-area">
              Room area, m² <span className="font-normal text-slate-500">(optional)</span>
            </Label>
            <Input
              id="household-area"
              inputMode="decimal"
              placeholder="24"
              aria-invalid={errors.room_area_m2 ? true : undefined}
              {...register("room_area_m2")}
            />
            <FieldError id="area-error">{errors.room_area_m2?.message}</FieldError>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="household-cadr">
              Purifier CADR, m³/h <span className="font-normal text-slate-500">(optional)</span>
            </Label>
            <Input
              id="household-cadr"
              inputMode="numeric"
              placeholder="300"
              disabled={!hasPurifier}
              {...register("purifier_cadr")}
            />
            <FieldError id="cadr-error">{errors.purifier_cadr?.message}</FieldError>
          </div>
        </div>

        <div className="mt-4 flex items-start gap-3">
          <Controller
            control={control}
            name="has_purifier"
            render={({ field }) => (
              <Checkbox
                id="household-purifier"
                checked={field.value}
                onCheckedChange={(checked) => field.onChange(checked === true)}
              />
            )}
          />
          <label htmlFor="household-purifier" className="cursor-pointer text-sm text-ink">
            The household uses an air purifier
          </label>
        </div>

        <fieldset className="mt-6 border-t border-line pt-5">
          <legend className="text-sm font-semibold text-ink">Household members</legend>
          <p className="mt-1 text-xs leading-relaxed text-ink-muted">
            Age bands and coarse flags only — no names, birth dates or diagnoses. Children (under
            18) and adults aged 60+ receive the sensitive-group precautions attributed in each
            recommendation.
          </p>

          <div className="mt-3 space-y-4">
            {fields.map((field, index) => {
              const memberErrors = errors.members?.[index];
              return (
                <fieldset
                  key={field.id}
                  className="rounded-xl border border-line bg-slate-50/50 p-4"
                >
                  <div className="flex items-center justify-between gap-2">
                    <legend className="text-sm font-semibold text-ink">Member {index + 1}</legend>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="text-red-700 hover:bg-red-50 hover:text-red-800"
                      disabled={fields.length === 1}
                      onClick={() => remove(index)}
                      aria-label={`Remove member ${index + 1}`}
                    >
                      <Trash2 className="size-3.5" aria-hidden="true" />
                      Remove
                    </Button>
                  </div>
                  <div className="mt-3 grid gap-4 sm:grid-cols-2">
                    <div className="flex flex-col gap-1.5">
                      <Label htmlFor={`member-${index}-age`}>Age band</Label>
                      <Select
                        id={`member-${index}-age`}
                        aria-invalid={memberErrors?.age_band ? true : undefined}
                        {...register(`members.${index}.age_band`)}
                      >
                        {AGE_BAND_OPTIONS.map((band) => (
                          <option key={band.value} value={band.value}>
                            {band.label}
                          </option>
                        ))}
                      </Select>
                      <FieldError id={`member-${index}-age-error`}>
                        {memberErrors?.age_band?.message}
                      </FieldError>
                    </div>
                    <fieldset className="flex flex-col gap-2 sm:row-span-4">
                      <legend className="text-sm font-medium text-ink">
                        Health flags <span className="font-normal text-slate-500">(optional)</span>
                      </legend>
                      <Controller
                        control={control}
                        name={`members.${index}.health_flags`}
                        render={({ field: flagsField }) => (
                          <div className="grid gap-1.5">
                            {HEALTH_FLAG_OPTIONS.map((flag) => {
                              const checked = flagsField.value.includes(flag.value);
                              const inputId = `member-${index}-flag-${flag.value}`;
                              return (
                                <div key={flag.value} className="flex items-start gap-2">
                                  <Checkbox
                                    id={inputId}
                                    checked={checked}
                                    onCheckedChange={(next) =>
                                      flagsField.onChange(
                                        next === true
                                          ? [...flagsField.value, flag.value]
                                          : flagsField.value.filter(
                                              (value) => value !== flag.value,
                                            ),
                                      )
                                    }
                                    className="mt-0.5 size-4"
                                  />
                                  <label
                                    htmlFor={inputId}
                                    className="cursor-pointer text-xs leading-snug text-ink-muted"
                                  >
                                    {flag.label}
                                  </label>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      />
                    </fieldset>
                  </div>
                </fieldset>
              );
            })}
          </div>

          {memberListError ? (
            <Alert variant="error" className="mt-3">
              <AlertDescription>{memberListError}</AlertDescription>
            </Alert>
          ) : null}

          <div className="mt-4 flex items-center justify-between gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => append({ age_band: "18-59", health_flags: [] })}
              disabled={fields.length >= 12}
            >
              <Plus className="size-4" aria-hidden="true" />
              Add member
            </Button>
            <p className="text-xs text-slate-500">{fields.length} of 12 members</p>
          </div>
        </fieldset>

        <div className="mt-6 border-t border-line pt-5">
          {healthConsent ? (
            <p className="text-xs leading-relaxed text-ink-muted">
              Health-data consent is recorded for this session. Selected flags are stored with the
              profile and can be removed by editing the members.
            </p>
          ) : (
            <div className="flex items-start gap-3">
              <Controller
                control={control}
                name="health_consent"
                render={({ field }) => (
                  <Checkbox
                    id="household-health-consent"
                    checked={field.value}
                    onCheckedChange={(checked) => field.onChange(checked === true)}
                  />
                )}
              />
              <div>
                <label
                  htmlFor="household-health-consent"
                  className="cursor-pointer text-sm font-medium text-ink"
                >
                  I consent to storing the selected general health flags
                </label>
                <p className="mt-1 text-xs leading-relaxed text-ink-muted">
                  Required only when a member has a health flag. The flags guide general
                  precautions; they are never treated as a medical assessment. You can save the
                  profile without any flags and skip this consent.
                </p>
                <FieldError id="health-consent-error">{errors.health_consent?.message}</FieldError>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-md text-xs leading-relaxed text-slate-500">
          Stored on the server under your anonymous session. Guidance is general, not medical
          advice.
        </p>
        <Button type="submit" disabled={busy || isSubmitting}>
          {busy ? "Saving…" : initial ? "Save profile changes" : "Create family profile"}
        </Button>
      </div>
    </form>
  );
}
