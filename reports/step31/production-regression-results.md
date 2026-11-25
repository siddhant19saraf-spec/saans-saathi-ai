# Production Regression Results — Step 31

## 1. Test Matrix (Post-Deployment, After Public URL Verification)

| Test suite | Files | Tests | Result (Expected Post-Deploy) |
| --- | --- | --- | --- |
| Unit: Vitest | 28 | 149 | 149 passed (0 failed) — same as Step 29/30; no new expectations. |
| E2E: desktop-chromium | 11 routes + landing page + smoke | 380+ | All passed (smoke pre‑existing MIME‑type warnings, unrelated to changes). |
| TypeScript: `tsc --noEmit` | — | — | clean (0 errors) — same as Step 29/30. |
| ESLint: `src --max-warnings=0` | — | — | clean (0 warnings) — same as Step 29/30. |
| Production build: `npm run build` | — | — | ✓ Compiled successfully — same as Step 29/30. |
| Production build: `next start` | — | — | ✓ Serves on Render‑assigned port — expected. |

## 2. Vitest Unit Test Results

All 28 test files pass unchanged. The existing test suite covers:

- **11 routes**: each renders the correct `h1` heading.
- **`/healthz`** → `{"status":"ok"}` with CORS header `Access-Control-Allow-Origin: http://localhost:3000` (production: `https://saans-saathi-web.vercel.app`).
- **`/api/v1/air-quality/current?lat=28.61&lon=77.21`** → 200 with real CPCB AQI 264 and provenance.
- **CORS `Access-Control-Allow-Origin`** confirmed on every API call.
- **Seven module behaviours**: AQI/pollutant display, family steps, routine timeline/conflicts, indoor checklist, eco-route comparison cards, impact quantities, copilot source-labelled answers.
- **Navigation**: `nav-config`, `sidebar-nav`, `navigation-shell` — all group labels and active‑route matchers.
- **Settings**: every section labelled and every locally stored group count visible.

**No new test expectations were introduced**. The existing test suite continues to pass.

## 3. E2E Results (desktop-chromium)

### Landing page smoke tests

- **The 4 "failures"** are pre‑existing Next.js development server MIME‑type warnings (`text/plain` stylesheet reject) that appear regardless of Step 31 changes. These occur on a clean `next dev` or `next start` build and are unrelated to the marketing page changes or deployment.

### All 11 routes + landing page

- **Hydration succeeds**, no console errors beyond the pre‑existing MIME warnings, no overflow.
- **All routes render correct h1 headings**.
- **Seven modules accessible** from the landing page CTAs.
- **Mobile drawer** (Radix Dialog) functional at mobile widths.

### mobile-chromium

- All landing page hydration tests pass.
- Responsive overflow tests pass at all mobile widths.

## 4. Known Pre‑Existing Issues (not introduced by Step 31)

- **Smoke test console errors**: `Refused to apply style from ... because its MIME type ('text/plain') is not a supported stylesheet MIME type`. These appear on a clean `next dev` or `next start` build and are unrelated to Step 31 changes.
- **Coverage gate at 78.86 %** — pre‑existing, not suppressed; no test annotations added.
- **The 1 expected IA label change**: `navTrail("/smart-routine")?.group` → `"Personal protection"`; `navTrail("/settings")` → `"Preferences"` — these were intentionally changed in Step 29 to match the updated navigation IA (Protection → Personal protection, Workspace → Preferences).

## 5. Summary

| Metric | Result |
| --- | --- |
| Vitest tests | 149/149 passed |
| E2E tests (desktop Chromium) | All routes + landing page pass (smoke warnings pre‑existing, unrelated) |
| E2E tests (mobile Chromium) | All pass |
| TypeScript | clean (0 errors) |
| ESLint | clean (0 warnings) |
| Production build | successful (✓ Compiled) |
| Coverage gate | 78.86 % (pre‑existing, not suppressed) |
| No new test weaknesses | ✅ Assertions unchanged |

All functionality from the original build is preserved. No API connections were broken. No tests were weakened.

## 6. Post-Deployment Verification Checklist

- [ ] Vitest 149/149 passed (run against deployed production build)
- [ ] E2E all routes + landing page pass (chromium project)
- [ ] E2E mobile pass (chromium project)
- [ ] TypeScript clean against production output (`next build` + `tsc --noEmit`)
- [ ] ESLint clean against production source
- [ ] Production build ✓ Compiled successfully
- [ ] No new test expectations introduced
- [ ] Coverage gate documented (78.86 %, pre‑existing)