import { z } from "zod";

import { apiRequest } from "@/lib/api/client";

export const apiMetaSchema = z
  .object({
    request_id: z.string().optional(),
    generated_at: z.string().optional(),
  })
  .optional();

export function apiEnvelope<T>(data: z.ZodType<T>) {
  return z.object({ data, meta: apiMetaSchema });
}

/** Call an endpoint that follows the `{ data, meta }` envelope. */
export async function apiData<T>(
  path: string,
  schema: z.ZodType<T>,
  options: {
    method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
    body?: unknown;
    signal?: AbortSignal;
  } = {},
): Promise<T> {
  const response = await apiRequest(path, {
    schema: apiEnvelope(schema),
    method: options.method,
    body: options.body,
    signal: options.signal,
  });
  return response.data;
}

/** Delete an endpoint that answers 204 No Content. */
export async function apiDelete(
  path: string,
  options: { signal?: AbortSignal } = {},
): Promise<void> {
  await apiRequest(path, { method: "DELETE", schema: z.undefined(), signal: options.signal });
}
