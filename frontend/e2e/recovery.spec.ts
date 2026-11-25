import { expect, test, type Page } from "@playwright/test";

/**
 * Website-recovery verification.
 *
 * Proves the production/dev build actually hydrates on every route:
 *   1. HTTP 200 and the route's exact <h1> becomes visible (scoped to <main>,
 *      so sidebar links can never satisfy the assertion).
 *   2. React claims the DOM (polled: the SSR streaming shell `<div hidden
 *      id="S:0">` must be revealed and the root `loading.tsx` fallback removed).
 *   3. The module loading skeleton is replaced by real content.
 *   4. Zero console errors and zero uncaught page errors.
 *
 * Run against an already-running server:
 *   E2E_BASE_URL=http://localhost:3001 npx playwright test e2e/recovery.spec.ts
 */

type Route = {
  path: string;
  /** Exact SSR <h1> text — must be visible inside <main> after hydration. */
  h1: string;
  /** Module loading skeleton that must be *gone* after hydration (null = none). */
  skeleton: string | null;
  /** The seven product modules (rest are shell/support routes). */
  module?: boolean;
};

/** Sidebar link label → route path, for client-side navigation clicks. */
const SIDEBAR_LABEL: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/air-quality": "Air intelligence",
  "/family": "Family intelligence",
  "/smart-routine": "SmartRoutine",
  "/indoor-shield": "IndoorShield",
  "/eco-route": "EcoRoute",
  "/impact": "Impact intelligence",
  "/copilot": "SAANS AI Copilot",
  "/settings": "Settings",
};

const ROUTES: Route[] = [
  { path: "/", h1: "Every Breath Matters. Every Decision Counts.", skeleton: "Loading content" },
  {
    path: "/dashboard",
    h1: "Today’s air intelligence",
    skeleton: "Loading your workspace",
    module: true,
  },
  {
    path: "/air-quality",
    h1: "Air quality in detail",
    skeleton: "Loading air intelligence",
    module: true,
  },
  { path: "/family", h1: "Family intelligence", skeleton: "Loading family intelligence", module: true },
  { path: "/smart-routine", h1: "SmartRoutine", skeleton: "Loading routine planner", module: true },
  { path: "/indoor-shield", h1: "IndoorShield", skeleton: "Loading indoor checklist", module: true },
  { path: "/eco-route", h1: "EcoRoute", skeleton: "Loading route preferences", module: true },
  { path: "/impact", h1: "Impact", skeleton: "Loading activity log", module: true },
  { path: "/copilot", h1: "SAANS AI Copilot", skeleton: null },
  { path: "/map", h1: "Choose a place on the map", skeleton: "Loading the map" },
  { path: "/settings", h1: "Settings", skeleton: "Loading settings" },
];

const MODULES = ROUTES.filter((r) => r.module);

function collectErrors(page: Page): { consoleErrors: string[]; pageErrors: string[] } {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  return { consoleErrors, pageErrors };
}

interface HydrationState {
  s0Exists: boolean;
  s0Hidden: boolean;
  rootLoadingStillPresent: boolean;
  withFiber: number;
  h1Visible: boolean;
}

async function hydrationState(page: Page): Promise<HydrationState> {
  return page.evaluate(() => {
    const s0 = document.getElementById("S:0");
    const rootLoading = Array.from(document.body.children).some(
      (c) => c.getAttribute?.("role") === "status",
    );
    const all = document.querySelectorAll("*");
    let withFiber = 0;
    for (const el of all) {
      if (Object.keys(el).some((k) => k.startsWith("__react"))) withFiber++;
    }
    const h1 = (document.querySelector("main h1") ?? document.querySelector("h1")) as HTMLElement | null;
    return {
      s0Exists: Boolean(s0),
      s0Hidden: s0 ? s0.hasAttribute("hidden") : false,
      rootLoadingStillPresent: rootLoading,
      withFiber,
      h1Visible: h1 ? Boolean(h1.offsetParent) : false,
    };
  });
}

/**
 * Poll until React has claimed the DOM. Hydration is asynchronous (the inline
 * `$RC` reveal fires from requestAnimationFrame and then React retries the
 * boundary), so a single eager sample on the slower dev server reads low.
 */
async function waitForHydration(page: Page, label: string, timeoutMs = 30_000): Promise<HydrationState> {
  const deadline = Date.now() + timeoutMs;
  let last = await hydrationState(page);
  while (Date.now() < deadline) {
    if (!last.s0Hidden && !last.rootLoadingStillPresent && last.withFiber > 50) return last;
    await page.waitForTimeout(250);
    last = await hydrationState(page);
  }
  throw new Error(
    `${label} did not hydrate within ${timeoutMs}ms: ${JSON.stringify(last)}`,
  );
}

test.describe("website recovery: all routes hydrate", () => {
  for (const route of ROUTES) {
    test(`${route.path} renders real content with no errors`, async ({ page }) => {
      const { consoleErrors, pageErrors } = collectErrors(page);

      const response = await page.goto(route.path, { waitUntil: "load" });
      expect(response?.status(), `${route.path} HTTP status`).toBe(200);

      // Exact h1 inside <main> must become visible (proves the shell revealed).
      const heading = page.getByRole("main").getByRole("heading", { level: 1, name: route.h1 });
      await expect(heading, `${route.path} h1 visible`).toBeVisible({ timeout: 25_000 });

      // React must claim the DOM (polled — not a single eager sample).
      const state = await waitForHydration(page, route.path);
      expect(state.s0Hidden, `${route.path} streaming shell #S:0 revealed`).toBe(false);
      expect(state.rootLoadingStillPresent, `${route.path} root loading fallback removed`).toBe(false);
      expect(state.withFiber, `${route.path} React-owned elements`).toBeGreaterThan(50);
      expect(state.h1Visible, `${route.path} h1 visible after hydration`).toBe(true);

      // Module loading skeleton must be replaced by real content.
      if (route.skeleton) {
        await expect(
          page.getByText(route.skeleton, { exact: false }).first(),
          `${route.path} skeleton replaced`,
        ).toHaveCount(0, { timeout: 15_000 });
      }

      // Real content must actually be rendered, not just a heading.
      const mainText = await page.getByRole("main").innerText();
      expect(mainText.length, `${route.path} main content length`).toBeGreaterThan(150);

      expect(consoleErrors, `${route.path} console errors`).toEqual([]);
      expect(pageErrors, `${route.path} page errors`).toEqual([]);
    });
  }
});

test.describe("website recovery: seven modules", () => {
  test("all seven modules are present in the navigation", async ({ page }) => {
    const { consoleErrors, pageErrors } = collectErrors(page);
    await page.goto("/dashboard", { waitUntil: "load" });
    await expect(
      page.getByRole("main").getByRole("heading", { level: 1, name: "Today’s air intelligence" }),
    ).toBeVisible({ timeout: 25_000 });
    await waitForHydration(page, "/dashboard nav");

    const hrefs = await page.evaluate(() =>
      Array.from(document.querySelectorAll("a[href]"))
        .map((a) => a.getAttribute("href"))
        .filter((h): h is string => Boolean(h)),
    );

    for (const route of MODULES) {
      expect(hrefs, `nav contains ${route.path}`).toContain(route.path);
    }
    expect(consoleErrors).toEqual([]);
    expect(pageErrors).toEqual([]);
  });

  test("client-side navigation between modules works", async ({ page }) => {
    const { consoleErrors, pageErrors } = collectErrors(page);
    await page.goto("/dashboard", { waitUntil: "load" });
    await expect(
      page.getByRole("main").getByRole("heading", { level: 1, name: "Today’s air intelligence" }),
    ).toBeVisible({ timeout: 25_000 });
    await waitForHydration(page, "/dashboard nav-start");

    for (const route of MODULES.slice(1, 4)) {
      // Below the lg breakpoint the sidebar lives in a drawer, so open it the
      // same way a mobile user would before reaching for a destination.
      const menuButton = page.getByRole("button", { name: "Open navigation menu" });
      if (await menuButton.isVisible()) {
        await menuButton.click();
      }

      // Click the sidebar link (sidebar is <nav>, outside <main>). Match the
      // sidebar label, not the page heading.
      await page
        .getByRole("navigation")
        .getByRole("link", { name: new RegExp(`^${escapeRegExp(SIDEBAR_LABEL[route.path]!)}$`, "i") })
        .first()
        .click();

      // Assert the URL changed FIRST — heading text is scoped to <main> so the
      // sidebar link can never satisfy it.
      await expect(page).toHaveURL(new RegExp(`${route.path}$`), { timeout: 20_000 });
      await expect(
        page.getByRole("main").getByRole("heading", { level: 1, name: route.h1 }),
      ).toBeVisible({ timeout: 20_000 });
      await waitForHydration(page, route.path);
    }

    expect(consoleErrors, "client navigation console errors").toEqual([]);
    expect(pageErrors, "client navigation page errors").toEqual([]);
  });
});

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
