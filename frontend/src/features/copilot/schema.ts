import { z } from "zod";

export const copilotActionSchema = z.object({
  title: z.string(),
  detail: z.string(),
  time_window: z.string().nullable(),
  fact_refs: z.array(z.string()),
  confidence: z.enum(["high", "medium", "low"]).nullable(),
});

export const copilotAvoidSchema = z.object({
  title: z.string(),
  reason_fact_ref: z.string().nullable(),
});

export const copilotCitationSchema = z.object({
  fact_id: z.string(),
  label: z.string(),
  value: z.union([z.number(), z.string()]).nullable(),
  unit: z.string().nullable(),
  source: z.string(),
  observed_at: z.string().nullable(),
});

export const copilotAnswerSchema = z.object({
  conversation_id: z.string(),
  message_id: z.string(),
  answer: z.string(),
  severity: z.string().nullable(),
  actions: z.array(copilotActionSchema),
  avoid: z.array(copilotAvoidSchema),
  citations: z.array(copilotCitationSchema),
  source: z.string(),
  model: z.string().nullable(),
  latency_ms: z.number().int().nonnegative().nullable(),
  disclaimer: z.string(),
});

export type CopilotAnswer = z.infer<typeof copilotAnswerSchema>;

export const copilotMessageSchema = z.object({
  message: z
    .string()
    .trim()
    .min(1, "Write a question first.")
    .max(800, "Keep the question under 800 characters."),
});

export type CopilotMessageValues = z.infer<typeof copilotMessageSchema>;
