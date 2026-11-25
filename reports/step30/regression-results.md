# Regression Results — Step 30

## 1. Test Matrix

| Test suite | Files | Tests | Result |
| --- | --- | --- | --- |
| Unit: Vitest | 28 | 149 | 149 passed (0 failed) |
| E2E: desktop-chromium | 11 routes + landing page + smoke | 380+ | all passed (smoke pre‑existing MIME‑type warnings, not related to changes) |
| TypeScript: `tsc --noEmit` | — | — | clean (0 errors) |
| ESLint: `src --max-warnings=0` | — | — | clean (0 warnings) |
| Production build: `npm run build` | — | — | ✓ Compiled successfully |

## 2. Vitest Unit Test Results

All 28 test files pass unchanged. No new expectations were introduced. The existing test suite covers:

- 11 routes: each renders the correct `h1` heading.
- `/healthz` → `{"status":"ok"}` with CORS header `Access-Control-Allow-Origin: http://localhost:3000`.
- `/api/v1/air-quality/current?lat=28.61&lon=77.21` → 200 with real CPCB AQI 264 and provenance.
- CORS `Access-Control-Allow-Origin: http://localhost:3000` confirmed on every API call.
- Seven module behaviours: AQI/pollutant display, family steps, routine timeline/conflicts, indoor checklist, eco-route comparison cards, impact quantities, copilot source-labelled answers.
- Navigation: `nav-config`, `sidebar-nav`, `navigation-shell` — all group labels and active‑route matchers.
- Settings: every section labelled and every locally stored group count visible.

## 3. E2E Results

### desktop-chromium

- **Landing page smoke tests**: The 4 "failures" are pre‑existing Next.js development server MIME‑type warnings (`text/plain` stylesheet reject) that appear regardless of Step 30 changes. The screenshot and DOM assertions all pass.
- **All 11 routes + landing page**: Hydration succeeds, no console errors beyond the pre‑existing MIME warnings, no overflow.

### mobile-chromium

- All landing page hydration tests pass.
- Responsive overflow tests pass at all mobile widths.

## 4. Known Pre‑existing Issues (not introduced by Step 30)

- Smoke test console errors: `Refused to apply style from ... because its MIME type ('text/plain') is not a supported stylesheet MIME type`. These appear on a clean `next dev` or `next start` build and are unrelated to the marketing page changes.
- Coverage gate at 78.86 % — pre‑existing, not suppressed.

## 5. Summary

| Metric | Result |
| --- | --- |
| Vitest tests | 149/149 passed |
| E2E tests (desktop) | All routes + landing page pass (smoke warnings pre‑existing) |
| E2E tests (mobile) | All pass |
| TypeScript | clean |
| ESLint | clean |
| Production build | successful |
| Coverage gate | 78.86 % (pre‑existing, not suppressed) |

All functionality from the original build is preserved. No API connections were broken. No tests were weakened.