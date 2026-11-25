import { expect, test } from "@playwright/test";

test("landing page renders the product identity", async ({ page }, testInfo) => {
  const consoleErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => consoleErrors.push(error.message));

  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Every Breath Matters/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /Open dashboard/i }).first()).toBeVisible();

  await page.screenshot({
    path: testInfo.outputPath("landing.png"),
    fullPage: true,
  });

  expect(consoleErrors).toEqual([]);
});

test("dashboard renders the daily briefing", async ({ page }, testInfo) => {
  const consoleErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => consoleErrors.push(error.message));

  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("dashboard.png"),
    fullPage: true,
  });

  expect(consoleErrors).toEqual([]);
});
