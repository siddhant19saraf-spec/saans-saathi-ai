import { z } from "zod";

/**
 * RFC 9457 problem details returned by the backend.
 *
 * `request_id` is optional because infrastructure-level failures may occur
 * before the application can attach one.
 */
export const problemSchema = z.object({
  type: z.string(),
  title: z.string(),
  status: z.number().int(),
  detail: z.string(),
  instance: z.string(),
  code: z.string(),
  request_id: z.string().nullish(),
});

export type Problem = z.infer<typeof problemSchema>;
