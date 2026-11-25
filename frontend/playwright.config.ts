import { defineConfig, devices } from "@playwright/test";

/**
 * E2E configuration.
 *
 * The frontend and backend must already be running:
 *   backend: uvicorn app.main:app --port 8000
 *   frontend: npm run dev (or npm run start after a build)
 *
 * Set E2E_BASE_URL to point at another deployment.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
  },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile-chromium", use: { ...devices["Pixel 7"] } },
  ],
});
