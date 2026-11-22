import { z } from "zod";

export const IMPACT_ACTIVITY_TYPES = [
  { value: "walked", label: "Walked or cycled instead of driving", unit: "km" },
  { value: "public-transport", label: "Used public transport", unit: "km" },
  { value: "worked-from-home", label: "Worked from home", unit: "days" },
  { value: "planted-tree", label: "Planted a tree", unit: "trees" },
] as const;

export type ImpactActivityType = (typeof IMPACT_ACTIVITY_TYPES)[number]["value"];

export const impactActivitySchema = z.object({
  id: z.string(),
  type: z.enum(["walked", "public-transport", "worked-from-home", "planted-tree"]),
  quantity: z.number().positive().max(100000),
  occurredOn: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
});

export const impactActivitiesSchema = z.array(impactActivitySchema).max(200);

export type ImpactActivity = z.infer<typeof impactActivitySchema>;

export const impactActivityFormSchema = z.object({
  type: z.enum(["walked", "public-transport", "worked-from-home", "planted-tree"]),
  quantity: z
    .string()
    .trim()
    .min(1, "Enter a quantity.")
    .refine((value) => {
      const parsed = Number(value);
      return Number.isFinite(parsed) && parsed > 0;
    }, "Enter a quantity greater than zero.")
    .refine((value) => Number(value) <= 100000, "Enter a quantity below 100,000."),
  occurredOn: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Choose the date the activity happened."),
});

export type ImpactActivityFormValues = z.input<typeof impactActivityFormSchema>;
export type ImpactActivityFormOutput = z.output<typeof impactActivityFormSchema>;

export function unitFor(type: ImpactActivityType): string {
  return IMPACT_ACTIVITY_TYPES.find((item) => item.value === type)?.unit ?? "units";
}

export function labelFor(type: ImpactActivityType): string {
  return IMPACT_ACTIVITY_TYPES.find((item) => item.value === type)?.label ?? "Activity";
}

export function toImpactActivity(values: ImpactActivityFormValues): ImpactActivity {
  return {
    id:
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    type: values.type,
    quantity: Number(values.quantity),
    occurredOn: values.occurredOn,
  };
}

export function todayLocalIso(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}
