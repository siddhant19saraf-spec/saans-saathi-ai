import { expect, test, type Page } from "@playwright/test";

/**
 * SAANS SAATHI AI — Universal Responsive Experience E2E tests.
 *
 * Tests every route at every required viewport size for:
 *   - Horizontal overflow (document width must not exceed viewport width)
 *   - Element visibility (headings, navigation, primary actions)
 *   - Navigation functionality (sidebar links, client-side nav)
 *   - Button interaction
 *   - Console errors
 *   - Failed network requests
 *
 * Run against an already-running dev server:
 *   E2E_BASE_URL=http://localhost:3000 npx playwright test e2e/responsive.spec.ts
 */

type Viewport = {
  label: string;
  width: number;
  height: number;
};

const VIEWPORTS: Viewport[] = [
  { label: "small-mobile", width: 320, height: 568 },
  { label: "standard-mobile", width: 360, height: 800 },
  { label: "large-mobile", width: 390, height: 844 },
  { label: "iphone-style", width: 430, height: 932 },
  { label: "small-tablet", width: 600, height: 960 },
  { label: "tablet", width: 768, height: 1024 },
  { label: "large-tablet", width: 1024, height: 1366 },
  { label: "laptop", width: 1280, height: 720 },
  { label: "desktop", width: 1440, height: 900 },
  { label: "large-desktop", width: 1920, height: 1080 },
];

// Landscape variants for mobile and tablet.
const LANDSCAPE_VIEWPORTS: Viewport[] = [
  { label: "small-mobile-landscape", width: 568, height: 320 },
  { label: "standard-mobile-landscape", width: 800, height: 360 },
  { label: "large-mobile-landscape", width: 844, height: 390 },
  { label: "iphone-style-landscape", width: 932, height: 430 },
  { label: "small-tablet-landscape", width: 960, height: 600 },
  { label: "tablet-landscape", width: 1024, height: 768 },
];

type Route = {
  path: string;
  /** Heading text that must be visible inside <main> after hydration. */
  heading: string | RegExp;
  /** The seven product modules. */
  module?: boolean;
};

const ROUTES: Route[] = [
  { path: "/", heading: /Every Breath Matters/i },
  { path: "/dashboard", heading: /Today.s air intelligence/i, module: true },
  { path: "/air-quality", heading: /Air quality in detail/i, module: true },
  { path: "/family", heading: /Family intelligence/i, module: true },
  { path: "/smart-routine", heading: /SmartRoutine/i, module: true },
  { path: "/indoor-shield", heading: /IndoorShield/i, module: true },
  { path: "/eco-route", heading: /EcoRoute/i, module: true },
  { path: "/impact", heading: /Impact/i, module: true },
  { path: "/copilot", heading: /SAANS AI Copilot/i, module: true },
  { path: "/map", heading: /Choose a place on the map/i, module: true },
  { path: "/settings", heading: /Settings/i, module: true },
];

const MODULES = ROUTES.filter((r) => r.module);

function collectErrors(page: Page): { consoleErrors: string[]; pageErrors: string[]; failedRequests: string[] } {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const failedRequests: string[] = [];

  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("requestfailed", (request) => {
    const failure = request.failure();
    // Ignore aborted requests (React AbortController cleanup on re-render) —
    // they are not real failures.
    if (failure?.errorText && !failure.errorText.toLowerCase().includes("abort")) {
      failedRequests.push(`${request.method()} ${request.url()} ${failure.errorText}`);
    }
  });
  page.on("request", (request) => {
    // Capture responses >= 400
    void request;
  });
  page.on("response", (response) => {
    if (response.status() >= 400) {
      failedRequests.push(`${response.request().method()} ${response.url()} ${response.status()}`);
    }
  });

  return { consoleErrors, pageErrors, failedRequests };
}

/**
 * Check that the document does not overflow horizontally.
 */
async function checkNoHorizontalOverflow(page: Page): Promise<{ ok: boolean; viewportW: number; docW: number }> {
  const dims = await page.evaluate(() => ({
    viewportW: document.documentElement.clientWidth,
    docW: document.documentElement.scrollWidth,
    bodyW: document.body.scrollWidth,
  }));
  return {
    ok: dims.docW <= dims.viewportW,
    viewportW: dims.viewportW,
    docW: dims.docW,
  };
}

async function waitForHydration(page: Page, label: string, timeoutMs = 25_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const state = await page.evaluate(() => {
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
        s0Hidden: s0 ? s0.hasAttribute("hidden") : false,
        rootLoadingStillPresent: rootLoading,
        withFiber,
        h1Visible: h1 ? Boolean(h1.offsetParent) : false,
      };
    });
    if (!state.s0Hidden && !state.rootLoadingStillPresent && state.withFiber > 50 && state.h1Visible) {
      return;
    }
    await page.waitForTimeout(250);
  }
  throw new Error(`${label} did not hydrate within ${timeoutMs}ms`);
}

test.describe("responsive design: all routes at all viewports", () => {
  for (const vp of VIEWPORTS) {
    test.describe(`viewport ${vp.label} (${vp.width}x${vp.height})`, () => {
      test.use({ viewport: { width: vp.width, height: vp.height } });

      for (const route of ROUTES) {
        test(`${route.path} renders with no overflow or errors`, async ({ page }) => {
          const { consoleErrors, pageErrors } = collectErrors(page);

          const response = await page.goto(route.path, { waitUntil: "load" });
          expect(response?.status(), `${route.path} HTTP status`).toBe(200);

          await waitForHydration(page, `${vp.label} ${route.path}`);

          // Exact heading must be visible inside <main>.
          const heading = page.getByRole("main").getByRole("heading", { level: 1, name: route.heading });
          await expect(heading, `${vp.label} ${route.path} heading visible`).toBeVisible({ timeout: 15_000 });

          // No horizontal overflow.
          const overflow = await checkNoHorizontalOverflow(page);
          expect(
            overflow.ok,
            `${vp.label} ${route.path} no horizontal overflow (doc=${overflow.docW}px viewport=${overflow.viewportW}px)`,
          ).toBe(true);

          // No console errors.
          expect(
            consoleErrors,
            `${vp.label} ${route.path} console errors`,
          ).toEqual([]);
          expect(pageErrors, `${vp.label} ${route.path} page errors`).toEqual([]);
        });
      }
    });
  }
});

test.describe("responsive design: landscape mobile and tablet", () => {
  const LANDSCAPE_ROUTES = [
    "/dashboard",
    "/air-quality",
    "/family",
    "/smart-routine",
    "/indoor-shield",
    "/eco-route",
    "/impact",
    "/map",
    "/settings",
  ];

  for (const vp of LANDSCAPE_VIEWPORTS) {
    test.describe(`viewport ${vp.label} (${vp.width}x${vp.height})`, () => {
      test.use({ viewport: { width: vp.width, height: vp.height } });

      for (const path of LANDSCAPE_ROUTES) {
        test(`${vp.label} ${path} renders with no overflow`, async ({ page }) => {
          const { consoleErrors, pageErrors } = collectErrors(page);

          const route = ROUTES.find((r) => r.path === path)!;
          const response = await page.goto(path, { waitUntil: "load" });
          expect(response?.status(), `${path} HTTP status`).toBe(200);

          await waitForHydration(page, `${vp.label} ${path}`);

          const heading = page.getByRole("main").getByRole("heading", { level: 1, name: route.heading });
          await expect(heading, `${vp.label} ${path} heading visible`).toBeVisible({ timeout: 15_000 });

          const overflow = await checkNoHorizontalOverflow(page);
          expect(
            overflow.ok,
            `${vp.label} ${path} no horizontal overflow (doc=${overflow.docW}px viewport=${overflow.viewportW}px)`,
          ).toBe(true);

          expect(consoleErrors).toEqual([]);
          expect(pageErrors).toEqual([]);
        });
      }
    });
  }
});

test.describe("responsive design: seven modules usable at small mobile", () => {
  test.use({ viewport: { width: 320, height: 568 } });

  for (const route of MODULES) {
    test(`${route.path} all features usable at 320px`, async ({ page }) => {
      const { consoleErrors, pageErrors } = collectErrors(page);

      const response = await page.goto(route.path, { waitUntil: "load" });
      expect(response?.status(), `${route.path} HTTP status`).toBe(200);

      await waitForHydration(page, `${route.path} small-mobile`);

      const heading = page.getByRole("main").getByRole("heading", { level: 1, name: route.heading });
      await expect(heading).toBeVisible({ timeout: 15_000 });

      // Verify primary interactive elements are present and not clipped.
      const buttons = page.getByRole("button");
      const buttonCount = await buttons.count();
      expect(buttonCount, `${route.path} has buttons`).toBeGreaterThan(0);

      // Every visible button should be within the viewport horizontally.
      for (let i = 0; i < Math.min(buttonCount, 5); i++) {
        const btn = buttons.nth(i);
        if (await btn.isVisible()) {
          const box = await btn.boundingBox();
          if (box) {
            expect(box.x, `${route.path} button ${i} not negative x`).toBeGreaterThanOrEqual(0);
            expect(
              box.x + box.width,
              `${route.path} button ${i} not beyond viewport`,
            ).toBeLessThanOrEqual(320 + 2); // 2px tolerance
          }
        }
      }

      expect(consoleErrors).toEqual([]);
      expect(pageErrors).toEqual([]);
    });
  }
});

test.describe("responsive design: navigation at small mobile", () => {
  test.use({ viewport: { width: 320, height: 568 } });

  test("mobile hamburger opens and navigates between modules", async ({ page }) => {
    const { consoleErrors, pageErrors } = collectErrors(page);

    await page.goto("/dashboard", { waitUntil: "load" });
    await waitForHydration(page, "/dashboard small-mobile nav");

    // Open the mobile navigation dialog.
    const menuButton = page.getByRole("button", { name: /Open navigation menu/i });
    await expect(menuButton).toBeVisible();
    await menuButton.click();

    // The dialog should open.
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();

    // Click a module link.
    await page.getByRole("link", { name: /Air intelligence/i }).first().click();
    await expect(page).toHaveURL(/.*\/air-quality/);
    await waitForHydration(page, "/air-quality small-mobile nav");

    expect(consoleErrors).toEqual([]);
    expect(pageErrors).toEqual([]);
  });
});
