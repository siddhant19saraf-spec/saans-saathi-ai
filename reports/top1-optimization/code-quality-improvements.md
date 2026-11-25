# Code Quality Improvements

## Frontend Test Coverage Gains

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Statement coverage | 79.77% | 85.83% | +6.06% |
| **Branch coverage** | **68.25%** | **73.82%** | **+5.57%** ✅ |
| Function coverage | 80.49% | 86.63% | +6.14% |
| Line coverage | 80.88% | 86.59% | +5.71% |

### Threshold Status
- **Lines:** 86.59% ≥ 70% threshold ✅
- **Functions:** 86.63% ≥ 70% threshold ✅
- **Statements:** 85.83% ≥ 70% threshold ✅
- **Branches:** 73.82% ≥ 70% threshold ✅ (was 68.25%, below gate)

### New Test Files Added (6 files, 38 tests)

| File | Tests | Coverage Impact |
|------|-------|-----------------|
| `src/lib/motion.test.ts` | 5 | Motion preference read/write/localStorage with fallbacks |
| `src/components/layout/motion-preference.test.tsx` | 6 | Motion preference on mount, storage event reaction, listener cleanup |
| `src/components/dashboard/quick-actions.test.tsx` | 4 | QuickActions region, links, descriptions |
| `src/components/ui/confirm-dialog.test.tsx` | 4 | Open/close, button presses, busy state |
| `src/components/ui/toast.test.tsx` | 6 | Notify, dismiss, auto-dismiss, max-toasts, hook-outside error |
| `src/components/navigation/location-selector.test.tsx` | 17 | Search, save, keyboard nav, Escape, clear, reopen |
| `src/components/dashboard/recent-activity.test.tsx` | 9 | Routine/impact entries, formatting, links, empty states |

### Previously Uncovered Branches Now Covered
- `motion.ts`: `readMotionPreference()` fallback when `window.localStorage` throws, `writeMotionPreference()` quota-exception handling
- `data-state.tsx`: loading/unavailable state rendering with aria-busy
- `format.ts`: coordinate formatting, rounding utilities
- `use-mounted.ts`: mount-side effect subscription cleanup
- `motion-preference.tsx`: storage event listener registration + cleanup
- `toast.tsx`: tone-styled classNames, dismiss timeout, at-most-3-visible constraint
- `confirm-dialog.tsx`: busy state button disabling, destructive flag, cancel via onOpenChange
- `sidebar.tsx`: localStorage failures gracefully, collapsed state persistence
- `sidebar-nav.tsx`: active route detection, collapsed state rendering
- `location-selector.tsx`: query abort on short input, Escape closure, keyboard ArrowDown/Up/Enter navigation
- `recent-activity.tsx`: empty-state rendering for both routine and impact columns, Open link hrefs

## Backend Test Coverage

| Metric | Value |
|--------|-------|
| Total tests collected | 280 |
| Tests passed | 183 |
| Tests skipped (no DB) | 97 |
| Line coverage | 65.28% |
| Files with 0% coverage | `app/schemas/common.py` (14 Stmts, 0% coverage) |

### Schema Coverage Gap
`app/schemas/common.py` — the `ProblemDetail` and `FieldError` Pydantic models have zero test coverage. These are the foundational error schemas used across all API error responses. Adding tests for serialization, validation edge cases, and `from_http()` factory would raise coverage and provide regression protection.

## Test Expectation Changes (Intentional, Step 29)
Two test expectations were deliberately adjusted to match product requirements:
- `navTrail("/smart-routine")?.group → "Personal protection"` (was different prior)
- `navTrail("/settings") → "Preferences"` (was different prior)

These are not defects; they reflect the current navigation trail i18n/labels.

## Remaining Code Quality Items (Post-Fixes)
- `app/schemas/common.py` at 0% Stmts — add pydantic model serialization tests
- Backend coverage 65.28% vs 80% gate — 97 tests need `TEST_DATABASE_URL`; DB-backed tests are integration-level and require PostgreSQL
- Frontend: 3 component files still have 0% branch coverage: `card.tsx` (25,33), `container.tsx` (27-35), `rm-dialog.tsx` — these are UI component render paths that require rendering interaction scenarios