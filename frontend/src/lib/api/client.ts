import { z } from "zod";

import { env } from "@/lib/env";
import { problemSchema } from "./problem";
import { readSessionToken } from "./session";

const DEFAULT_TIMEOUT_MS = 10_000;

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | null;

  constructor(args: { message: string; status: number; code: string; requestId?: string | null }) {
    super(args.message);
    this.name = "ApiError";
    this.status = args.status;
    this.code = args.code;
    this.requestId = args.requestId ?? null;
  }
}

export type ApiRequestOptions<T> = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  /** Every response is parsed at runtime; never trust the network shape. */
  schema: z.ZodType<T>;
  signal?: AbortSignal;
  timeoutMs?: number;
  /** Attach the anonymous bearer token when one exists (default: true). */
  auth?: boolean;
};

/**
 * Minimal typed HTTP client.
 *
 * Responsibilities: absolute URL construction, JSON encoding, timeout,
 * RFC 9457 error mapping and response validation. No domain logic.
 */
export async function apiRequest<T>(path: string, options: ApiRequestOptions<T>): Promise<T> {
  const url = new URL(path, `${env.NEXT_PUBLIC_API_BASE_URL}/`);
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const forwardAbort = () => controller.abort();

  options.signal?.addEventListener("abort", forwardAbort, { once: true });

  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (options.auth !== false) {
    const token = readSessionToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: controller.signal,
      cache: "no-store",
    });
  } catch {
    const timedOut = controller.signal.aborted && !options.signal?.aborted;
    throw new ApiError({
      message: timedOut
        ? `Request timed out after ${timeoutMs} ms.`
        : "The API could not be reached.",
      status: 0,
      code: timedOut ? "REQUEST_TIMEOUT" : "NETWORK_ERROR",
    });
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", forwardAbort);
  }

  const contentType = response.headers.get("content-type") ?? "";
  const payload: unknown =
    response.status === 204
      ? undefined
      : contentType.includes("json")
        ? await response.json().catch(() => null)
        : await response.text();

  if (!response.ok) {
    const problem = problemSchema.safeParse(payload);
    if (problem.success) {
      throw new ApiError({
        message: problem.data.detail,
        status: problem.data.status,
        code: problem.data.code,
        requestId: problem.data.request_id ?? null,
      });
    }
    throw new ApiError({
      message: `Request failed with status ${response.status}.`,
      status: response.status,
      code: "UNKNOWN_ERROR",
    });
  }

  return options.schema.parse(payload);
}
