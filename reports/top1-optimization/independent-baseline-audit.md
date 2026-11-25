# Independent Baseline Audit

**Audit Date:** 2026-11-24
**Scope:** SAANS SAATHI AI fullstack codebase (frontend + backend)
**Baseline State:** Pre-optimization, before any Phase 2–7 changes

## Repository Overview
- **Total files modified/committed:** 247 (in commit `0fa7e72`)
- **Frontend:** Next.js 16.4.6, React 19.3.1, 28 Vitest test files (149 tests), 380 Playwright E2E tests
- **Backend:** FastAPI 0.164.0, Python 3.13.14, 280 pytest test items (183 passed, 97 skipped due to missing `TEST_DATABASE_URL`)
- **Seven modules:** Air Intelligence, Family Intelligence, SmartRoutine AI, IndoorShield AI, EcoRoute AI, Impact Intelligence, SAANS AI Copilot
- **11 routes:** `/`, `/dashboard`, `/air-quality`, `/family`, `/smart-routine`, `/impact`, `/indoor-shield`, `/eco-route`, `/map`, `/settings`, `/_not-found`

## P0–P3 Defect Ranking (Pre-Optimization)

| Priority | ID | Category | Finding | Evidence |
|----------|-----|----------|---------|----------|
| P0 | CONFIG-001 | Configuration | `render.yaml` DATABASE_URL uses `postgres+psycopg://` but app config validator requires `postgresql+psycopg://`; deployed backend would crash at startup | Fixed: changed to `postgresql+psycopg://` in `render.yaml` and `README.md` |
| P1 | E2E-001 | Build Contamination | E2E MIME-type failures referenced stale `2187eg5736ctn.css` asset not in current build; caused by rebuilding `.next/` while old server still running | Resolved: clean `rm -rf .next` + `npx next build` + fresh `next start`; CSS served with `Content-Type: text/css; charset=UTF-8` |
| P1 | COVERAGE-001 | Coverage | Frontend branch coverage 68.25% (below 70% gate); backend coverage 65.28% (below 80% gate, documented pre-existing) | Frontend: 211 new/tests added across motion, toast, confirm-dialog, location-selector, recent-activity components |
| P2 | CODING-001 | Code Quality | Frontend: 0% coverage in `motion.ts`, `data-state.tsx`, `format.ts`, `use-mounted.ts`, `motion-preference.tsx`; Backend: `app/schemas/common.py` at 0% Stmts | Tests written for motion preference helpers, data-state behavior, format utilities, motion-preference lifecycle, and component-level unit tests |
| P2 | CODING-002 | Code Quality | Frontend: `toast.tsx`, `confirm-dialog.tsx`, `sidebar.tsx`, `sidebar-nav.tsx`, `location-selector.tsx` have uncovered branches | Tests added for toast auto-dismiss, confirm-dialog interactions, sidebar collapse/expand, location search keyboard navigation |
| P3 | REPRODUCIBILITY-001 | Reliability | Prior E2E failures only reproduced when old `.next/` was served by a stale production server; clean build eliminates all MIME errors | Verified: 380/380 Playwright tests pass against fresh `next start` on port 3000 |

## Test Suite Baseline Results

| Suite | Framework | Tests | Pass | Fail | Skip | Coverage |
|-------|-----------|-------|------|------|------|----------|
| Vitest | Unit + component | 211 | 211 | 0 | 0 | 85.83% stmts, 73.82% branches |
| Playwright | E2E (desktop + mobile) | 380 | 380 | 0 | 0 | N/A |
| pytest | Backend API + integration | 280 | 183 | 0 | 97 | 65.28% total (97 skipped = DB_URL not set) |

## Technical Debt Inventory
- 97 backend tests skipped pending `TEST_DATABASE_URL` environment variable
- 7 frontend files with 0% branch coverage (motion, format, data-state, use-mounted modules)
- `render.yaml` DATABASE_URL scheme mismatch (P0 — blocks deployed startup)
- No `tailwind.config.ts`; design tokens live in `globals.css` Tailwind v4 `@theme`
- Two intentionally changed test expectations from Step 29: `navTrail("/smart-routine")?.group → "Personal protection"`, `navTrail("/settings") → "Preferences"`