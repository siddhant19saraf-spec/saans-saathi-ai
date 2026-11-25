import { z } from "zod";

/**
 * Public (browser-visible) configuration.
 *
 * Only NEXT_PUBLIC_* values belong here. Server secrets must never be added to
 * this schema because Next.js inlines these values into the client bundle.
 */
// `z.httpUrl()` rejects hostnames without a public suffix, which makes the
// documented local default (`http://localhost:8000`) invalid. `z.url()` with
// an explicit protocol allowlist accepts localhost and loopback addresses
// while still rejecting non-HTTP schemes.
const httpUrl = z.url({ protocol: /^https?$/ });

const publicEnvSchema = z.object({
  NEXT_PUBLIC_API_BASE_URL: httpUrl.default("http://localhost:8000"),
});

const parsed = publicEnvSchema.safeParse({
  NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
});

if (!parsed.success) {
  throw new Error(
    "Invalid frontend environment configuration. Check NEXT_PUBLIC_API_BASE_URL in frontend/.env.local.",
  );
}

export const env = parsed.data;
