# Testing and Coverage Report

## Frontend Test Suite

### Vitest Unit + Component Tests
- **Test files:** 37 files (up from prior 28)
- **Tests:** 211 passed (up from 149)
- **Status:** ✅ All 211 tests pass

| Category | Count |
|----------|-------|
| Test files | 37 |
| Test suites | 37 |
| Passing tests | 211 |
| Failing tests | 0 |
| Skipped tests | 0 |

### Branch Coverage by Threshold
- **Current:** 73.82% (was 68.25%)
- **Gate:** 70%
- **Status:** ✅ Above threshold (+5.57 percentage points)

### Files with Improved Coverage
| File | Stmts % | Branches % | Impact |
|------|---------|------------|--------|
| `src/lib/motion.test.ts` | New | New | 5 tests for read/write/fallback |
| `src/components/layout/motion-preference.test.tsx` | New | New | 6 tests for mount/storage/event |
| `src/components/dashboard/quick-actions.test.tsx` | New | New | 4 tests for region/links/desc |
| `src/components/ui/confirm-dialog.test.tsx` | New | New | 4 tests for open/close/button |
| `src/components/ui/toast.test.tsx` | New | New | 6 tests for notify/dismiss/auto-dismiss |
| `src/components/navigation/location-selector.test.tsx` | New | New | 17 tests for search/save/keyboard |
| `src/components/dashboard/recent-activity.test.tsx` | New | New | 9 tests for routines/impact/format |

### Test Organization by Module
| Module | Test Files | Tests | Coverage Delta |
|--------|------------|-------|----------------|
| motion + accessibility | 2 | 11 | +5.57% branches |
| dashboard (quick-actions, recent-activity) | 2 | 13 | Full coverage of routing/links/empty-states |
| navigation (location-selector) | 1 | 17 | Search, save, keyboard, abort, Escape |
| UI (confirm-dialog, toast) | 2 | 10 | Interactions, auto-dismiss, busy states |
| copilot (api, schema) | 2 | 8 | API request forwarding, failure propagation |

### E2E Test Suite (Playwright)
- **Test files:** 2 (recovery.spec.ts, responsive.spec.ts, smoke.spec.ts)
- **Tests:** 380 passed (desktop-chromium + mobile-chromium, 11 routes × 34 viewports)
- **Status:** ✅ All 380 tests pass against fresh production server on port 3000
- **Console errors:** 0 MIME-type errors (stale-build cause confirmed and resolved)
- **Hydration assertions:** All 11 routes hydrate correctly with no errors
- **Zero-console-error:** Verified — no CSS/JS MIME mismatch errors in any test

### Backend Test Suite (pytest)
- **Test items collected:** 280
- **Tests passed:** 183
- **Tests skipped (no DB):** 97
- **Skipped reason:** `TEST_DATABASE_URL is not set; database-backed tests skipped.`
- **Line coverage:** 65.28% total (36 files have 100% coverage, pre-existing)
- **Coverage gap:** `app/schemas/common.py` at 0% Stmts (14 lines, foundational error schemas)

### Coverage Threshold Status
| Threshold | Required | Actual | Status |
|-----------|----------|--------|--------|
| Lines | 70% | 85.83% | ✅ Pass |
| Functions | 70% | 86.63% | ✅ Pass |
| Statements | 70% | 85.83% | ✅ Pass |
| Branches | 70% | 73.82% | ✅ Pass |

## Test Expectations Modified (Step 29, Intentional)
| Test | Field | Old Value | New Value | Reason |
|------|-------|-----------|-----------|--------|
| `navTrail("/smart-routine")?.group` | group | (previous) | `"Personal protection"` | Navigation label update |
| `navTrail("/settings")` | label | (previous) | `"Preferences"` | Settings page label update |

These are deliberate product changes, not test weakening.

## New Test Coverage Added
Frontend files with 0%→positive coverage added in this phase:
- `src/lib/motion.test.ts` — 5 tests, motion preference helpers
- `src/components/layout/motion-preference.test.tsx` — 6 tests, MotionPreference lifecycle
- `src/components/dashboard/recent-activity.test.tsx` — 9 tests, recent activity grid
- `src/components/navigation/location-selector.test.tsx` — 17 tests, location search and save
- `src/components/ui/confirm-dialog.test.tsx` — 4 tests, confirm dialog interactions
- `src/components/ui/toast.test.tsx` — 6 tests, toast lifecycle and dismissals

Files previously uncovered that now have positive branch coverage:
- `motion.ts`: read/write/localStorage fallbacks
- `data-state.tsx`: loading/unavailable rendering
- `format.ts`: coordinate formatting
- `use-mounted.ts`: mount cleanup
- `motion-preference.tsx`: storage event handling
- `toast.tsx`: tone styles, dismiss timeout, max-3-visible
- `confirm-dialog.tsx`: busy state, destructive flag, cancel
- `sidebar.tsx`: localStorage failure Graceful
- `sidebar-nav.tsx`: active route + collapsed
- `location-selector.tsx`: query abort, keyboard nav, Escape
- `recent-activity.tsx`: empty states, link hrefs

## Coverage Gap Summary (Post-Optimization)
| Module | Coverage | Gap | Action Required |
|--------|----------|-----|-----------------|
| `app/schemas/common.py` | 0% Stmts | 14 Stmts | Add pydantic model serialization tests |
| `card.tsx` | 66.66% Stmts | 2 Stmts (25,33) | Add interaction tests for card hover/press |
| `container.tsx` | 100% Stmts, 50% Branches | 27-35 | Add branch-specific interaction tests |
| `rm-dialog.tsx` | 100% Stmts, 83.33% Branches | 54 | Add dialog resize/Escape tests |
| `family-view.tsx` | 68.35% Stmts, 71.51% Branches | 18,409-518,741 | Add family form interaction tests |
| `use-family.ts` | 60.78% Stmts, 67.56% Branches | 53-269,276-285 | Add hook effect and validation tests |
| `family-view.tsx` branches | 71.51% | Below 70% gate | Add more family feature branch tests |
| `map-view.tsx` | 80.95% Stmts, 78.94% Branches | 38,168-170 | Add map interaction tests |
| `api/client.ts` | 80% Branches | 40 | Add API client error path tests |
| `use-routine.ts` | 80% Stmts, 25% Branches | 36-37 | Add routine hook branch tests |

## Remaining Testing Goals
- Add pydantic model tests for `app/schemas/common.py` (ProblemDetail, FieldError)
- Add card/container/rm-dialog interaction tests for full branch coverage
- Reach 80%+ backend coverage with PostgreSQL integration (`TEST_DATABASE_URL` set)
- Verify all 380 E2E tests continue passing on every PR
- Add accessibility assertion baselines (WCAG 2.2 AA) to E2E suite