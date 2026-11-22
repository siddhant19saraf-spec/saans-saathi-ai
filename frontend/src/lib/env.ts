import { z } from "zod";

/**
 * Public (browser-visible) configuration.
 *
 * Only NEXT_PUBLIC_* values belong here. Server secrets must never be added to
 * this schema because Next.js inlines these values into the client bundle.
 */
const publicEnvSchema = z.object({
  NEXT_PUBLIC_API_BASE_URL: z.httpUrl().default("http://localhost:8000"),
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
