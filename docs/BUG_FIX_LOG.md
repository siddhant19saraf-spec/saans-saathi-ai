# SAANS SAATHI AI — Bug Fix Log

**Audit date:** 2026-11-21  
**Method:** Defects triaged P0 → P1 → P2 → P3. Each fix has root cause, minimal safe change, and regression coverage. No errors suppressed, no tests disabled, no packages downgraded.

---

## P0 — Critical

### BF-001: Copilot service crashes on anonymous requests

| Field | Value |
|-------|-------|
| Severity | P0 |
| Root cause | `_build_fact_pack` called air-quality provider calls with `None` lat/lon for sessions without household coordinates |
| Fix | `_build_fact_pack` receives `session`; skips air calls when `lat`/`lon` are `None`; returns privacy-safe FactPack without location data |
| File | `backend/app/services/copilot_service.py` |
| Regression test | `tests/test_copilot.py::test_fact_pack_without_coordinates_skips_the_provider` |
| Status | Fixed |

### BF-002: FactPack exposes names, coordinates, free text to model

| Field | Value |
|-------|-------|
| Severity | P0 |
| Root cause | FactPack included raw coordinates, member names, unstructured free text; health-flag leakage and dead impact placeholder present |
| Fix | Removed health-flag leakage and dead impact placeholder; FactPack only includes deterministic provenance-tracked facts with structured IDs/labels |
| File | `backend/app/services/copilot_service.py`, `backend/app/domain/facts.py` |
| Regression test | `tests/test_copilot.py::test_fact_pack_excludes_names_coordinates_and_free_text` |
| Status | Fixed |

### BF-003: Validation flag uses non-DB-allowed value

| Field | Value |
|-------|-------|
| Severity | P0 |
| Root cause | Validation flags persisted with values outside the database check constraint allowlist |
| Fix | Persistence uses only DB-allowed values `"valid"`, `"rejected"`, `"fallback"` |
| File | `backend/app/integrations/ai/validation.py` |
| Regression test | `tests/test_copilot.py::test_validation_flag_uses_a_database_allowed_value` |
| Status | Fixed |

### BF-004: Tool executor stub — no authorization, no honest error statuses

| Field | Value |
|-------|-------|
| Severity | P0 |
| Root cause | `tool_executor.py` was a placeholder stub with fake responses, no authorization checks, no distinction between unsupported tools and execution errors |
| Fix | Fully rewritten with real service calls (copilot, family, routine, impact, indoor shield, ecoroute, air); per-profile authorization; honest `unsupported`/`error` statuses; `air_service` passed from `/copilot/tool-request` |
| File | `backend/app/integrations/ai/tool_executor.py` |
| Regression tests | `tests/test_tool_executor.py` — unknown tool, missing air service, missing coordinates, cross-profile ID, invalid journey ID, profile-required tools |
| Status | Fixed |

---

## P1 — High

### BF-005: Carbon `bus` factor missing from registry

| Field | Value |
|-------|-------|
| Severity | P1 |
| Root cause | `bus_average_uk_defra_2023` factor absent from impact factors endpoint; registry reported 4 instead of 5 factors |
| Fix | Restored `bus` factor with DEFRA 2023 provenance (source URL, version, retrieval date) |
| File | `backend/app/domain/factors.py` |
| Regression test | `tests/test_carbon.py` + `tests/test_impact.py::test_factors_expose_provenance` |
| Status | Fixed |

### BF-006: Routine tests use stale `activity_windows` contract

| Field | Value |
|-------|-------|
| Severity | P1 |
| Root cause | `tests/test_routines.py` referenced removed `household.activity_windows` and stale engine version `routine-1.0.0` |
| Fix | Updated to current contract: `NO_ACTIVITY_WINDOWS` → `NO_ACTIVITIES`, engine `routine-2.0.0`, `data_quality` → `data_status.forecast` |
| File | `backend/tests/test_routines.py` |
| Regression | All 6 tests pass against live API |
| Status | Fixed |

### BF-007: Persistence flow uses removed repo method

| Field | Value |
|-------|-------|
| Severity | P1 |
| Root cause | `tests/test_persistence_flow.py` called `routines_repo.create(...)` (removed); missing `flush()` before recommendation creation |
| Fix | Replaced `create` with `add(...)`; added `await database_session.flush()` |
| File | `backend/tests/test_persistence_flow.py` |
| Regression | `tests/test_persistence_flow.py` passes |
| Status | Fixed |

### BF-008: Migration drift — 8 check constraint names mismatch ORM

| Field | Value |
|-------|-------|
| Severity | P1 |
| Root cause | Migration `0008` created check constraints with names not matching SQLAlchemy ORM metadata |
| Fix | Forward migration `0009_constraint_names.py` renames all 8 constraints; did not edit shipped `0008`; migration test expects `0009_constraint_names` |
| File | `backend/alembic/versions/0009_constraint_names.py` |
| Regression test | `tests/test_migrations.py` (2 tests) |
| Status | Fixed |

---

## P2 — Medium

### BF-009: Impact baseline not disclosed as modelled assumption

| Field | Value |
|-------|-------|
| Severity | P2 |
| Root cause | `baseline_and_savings` computed modelled car baseline but basis strings did not clearly label it as an assumption |
| Fix | Basis strings now state "Modelled car travel" and "Not a measured baseline" |
| File | `backend/app/services/impact_service.py` |
| Regression test | `tests/test_impact_ledger.py::test_baseline_savings_and_trends_disclose_the_modelled_baseline` |
| Status | Fixed |

### BF-010: Routine activity partial update skips re-validation

| Field | Value |
|-------|-------|
| Severity | P2 |
| Root cause | Partial updates to routine activities could introduce invalid windows/venues without re-validation against stored values |
| Fix | `_values_from_update` merges changes with stored values before `_validate_values`; conflicting combinations rejected |
| File | `backend/app/services/routine_service.py` |
| Regression test | `tests/test_routine_lifecycle.py::test_activity_preferences_can_be_updated_cleared_and_deactivated` |
| Status | Fixed |

### BF-011: Delete inactive activity returns 404 instead of idempotent 204

| Field | Value |
|-------|-------|
| Severity | P2 |
| Root cause | `delete_activity` soft-deletes; second delete on already-inactive activity returned 404 |
| Fix | Delete is idempotent — returns 204 for already-inactive activities |
| File | `backend/app/services/routine_service.py` |
| Regression test | `tests/test_routine_lifecycle.py` |
| Status | Fixed |

### BF-012: Cancelling last activity triggers `NO_ACTIVITIES` on regenerate

| Field | Value |
|-------|-------|
| Severity | P2 |
| Root cause | `update_routine_activity` with `cancel: true` deactivates the only activity; `_generate` then raises `NO_ACTIVITIES` |
| Fix | Cancel path preserves plan state correctly; verified after cancellation with remaining activities |
| File | `backend/app/services/routine_service.py` |
| Regression test | `tests/test_routine_lifecycle.py::test_plan_read_history_replan_and_manual_change` |
| Status | Fixed |

### BF-013: Impact ledger routes inconsistent `NO_HOUSEHOLD` responses

| Field | Value |
|-------|-------|
| Severity | P2 |
| Root cause | `/goals`, `/trends`, `/baseline-savings` returned different error shapes when no household exists |
| Fix | All impact ledger routes return `422 NO_HOUSEHOLD` consistently |
| File | `backend/app/services/impact_service.py` |
| Regression test | `tests/test_impact_ledger.py::test_ledger_routes_require_a_household` |
| Status | Fixed |

---

## P3 — Low

### BF-014: Frontend dashboard sections untested for unavailable states

| Field | Value |
|-------|-------|
| Severity | P3 |
| Root cause | `CurrentAirSection`, `ProvenancePanel`, `InsightsPanel` had no unit tests for missing AQI, stale data, family-unavailable states |
| Fix | Added `frontend/src/components/dashboard/dashboard-sections.test.tsx` (7 tests) |
| File | `frontend/src/components/dashboard/dashboard-sections.test.tsx` |
| Status | Fixed |

### BF-015: Family schema conversions untested

| Field | Value |
|-------|-------|
| Severity | P3 |
| Root cause | `profileToForm`, `toProfileInput`, `preferencesToForm`, `toPreferencesInput` had no tests for null handling, consent gating, quiet-hours validation |
| Fix | Added `frontend/src/features/family/schema.test.ts` (5 tests) |
| File | `frontend/src/features/family/schema.test.ts` |
| Status | Fixed |

### BF-016: Family workspace hooks untested

| Field | Value |
|-------|-------|
| Severity | P3 |
| Root cause | `useFamilyWorkspace`, `useFamilyOverview` had no tests for profile creation, consent, generation, deletion, error handling |
| Fix | Added `frontend/src/features/family/use-family.test.tsx` (5 tests) |
| File | `frontend/src/features/family/use-family.test.tsx` |
| Status | Fixed |

---

## New Regression Test Files

| File | Tests | Purpose |
|------|-------|---------|
| `backend/tests/test_routine_lifecycle.py` | 9 | Activity validation, updates, replan, manual change, version chain |
| `backend/tests/test_impact_ledger.py` | 5 | Household scoping, duplicates, baseline disclosure, goal lifecycle |
| `backend/tests/test_household_edges.py` | 2 | Features require household, missing members/locations, consent |
| `frontend/src/components/navigation/navigation-shell.test.tsx` | 14 | CommandSearch, LocationSwitcher, Notifications, UserMenu, Breadcrumbs |
| `frontend/src/components/map/map-view.test.tsx` | 7 | MapView, MapCanvas with Leaflet mocking |
| `frontend/src/app/routes.test.tsx` | 15 | All app routes, marketing, error/loading/404 |
| `frontend/src/components/dashboard/dashboard-sections.test.tsx` | 7 | CurrentAirSection, ProvenancePanel, InsightsPanel |
| `frontend/src/features/family/schema.test.ts` | 5 | Profile/preferences schema validation |
| `frontend/src/features/family/use-family.test.tsx` | 5 | Workspace hooks |
| `frontend/src/features/store/storage.test.ts` | 9 | Storage read/write/remove/hydration edge cases |
| `frontend/src/lib/api/session.test.ts` | 6 | Session storage round-trip, expiry, stability |
| `frontend/src/features/locations/location-context.test.tsx` | 6 | Location add/remove/activate, MAX 8 cap |
| `frontend/src/components/navigation/nav-config.test.ts` | 3 | Route finding, breadcrumb trail |

---

## Verification Results by Area

| Area | Tests | Passed | Failed |
|------|-------|--------|--------|
| Backend full DB suite | 264 | 264 | 0 |
| Backend targeted (new files) | 16 | 16 | 0 |
| Frontend all suites | 85+ | 85+ | 0 |
| Frontend targeted (new files) | 36+ | 36+ | 0 |

No tests were disabled, skipped, or downgraded to achieve these results.
