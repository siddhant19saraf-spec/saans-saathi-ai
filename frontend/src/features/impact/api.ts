import { z } from "zod";

import { apiData } from "@/features/api/client";

export const factorSchema = z.object({
  key: z.string(),
  label: z.string(),
  value: z.number(),
  unit: z.string(),
  source: z.string(),
  source_url: z.url(),
  version: z.string(),
  retrieved_at: z.string().optional(),
});

export type EmissionFactor = z.infer<typeof factorSchema>;

const factorsSchema = z.array(factorSchema);

export function fetchFactors(signal: AbortSignal): Promise<EmissionFactor[]> {
  return apiData("/api/v1/impact/factors", factorsSchema, { signal });
}
