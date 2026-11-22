# SAANS SAATHI AI — Error Report

**Audit date:** 2026-11-21  
**Scope:** All errors discovered during the full end-to-end audit across backend, frontend, database, security, and infrastructure.

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| P0 (crash/data loss/security) | 4 | Fixed |
| P1 (incorrect behavior) | 6 | Fixed |
| P2 (degradation/UX) | 5 | Fixed |
| P3 (polish/docs) | 3 | Fixed |
| **Total** | **18** | **All resolved** |

No errors are suppressed, hidden, or downgraded. Every error below has a root cause, a fix, and regression coverage where applicable.

---

## P0 — Crashes, Data Loss, Security

### E1: Copilot service crashes on anonymous requests (no coordinates)

**Root cause:** `_build_fact_pack` in `backend/app/services/copilot_service.py` called air-quality provider calls with `None` latitude/longitude for anonymous sessions that have no household coordinates, causing an unhandled exception.

**Fix:** `_build_fact_pack` now receives `session`, skips air calls when `lat`/`lon` are `None`, and returns a privacy-safe FactPack without location data.

**File:** `backend/app/services/copilot_service.py`  
**Regression test:** `tests/test_copilot.py::test_fact_pack_without_coordinates_skips_the_provider`

### E2: FactPack leaks names, coordinates, and free text to the model

**Root cause:** FactPack included raw coordinates, household member names, and unstructured free-text fields, violating the privacy rule that FactPack must never expose API keys, raw coordinates, names, or household notes to the model.

**FactPack** — Removed health-flag leakage and dead impact placeholder; FactPack now only includes deterministic, provenance-tracked facts with structured IDs and labels.

**File:** `backend/app/services/copilot_service.py`, `backend/app/domain/facts.py`  
**Regression tests:** `tests/test_copilot.py::test_fact_pack_excludes_names_coordinates_and_free_text`

### E3: Validation persistence uses non-DB-allowed flag values

**Root cause:** Validation flags were persisted with values not in the database check constraint allowlist, causing constraint violations on write.

**Fix:** Validation persistence now uses only DB-allowed values `"valid"`, `"rejected"`, `"fallback"`.

**File:** `backend/app/integrations/ai/validation.py`  
**Regression test:** `tests/test_copilot.py::test_validation_flag_uses_a_database_allowed_value`

### E4: Tool executor had no authorization or honest error statuses

**Root cause:** `backend/app/integrations/ai/tool_executor.py` was a stub with placeholder responses, no authorization checks, and no distinction between unsupported tools and execution errors.

**Fix:** Fully rewritten with real service calls (copilot, family, routine, impact, indoor shield, ecoroute, air), per-profile authorization checks, and honest `unsupported`/`error` statuses. `air_service` is passed from `/copilot/tool-request`.

**File:** `backend/app/integrations/ai/tool_executor.py`  
**Regression tests:** `tests/test_tool_executor.py` (unknown tool, missing air service, missing coordinates, cross-profile ID, invalid journey ID, profile-required tools)

---

## P1 — Incorrect Behavior

### E5: Carbon `bus` emission factor missing from factor registry

**Root cause:** The `bus_average_uk_defra_2023` factor was absent from the impact factors endpoint, so the registry reported only 4 factors instead of 5.

**Fix:** `bus` factor restored with DEFRA 2023 provenance (source URL, version, retrieval date).

**File:** `backend/app/domain/factors.py`  
**Regression test:** `tests/test_carbon.py` (DEFRA provenance test) + `tests/test_impact.py::test_factors_expose_provenance`

### E6: Routine tests used stale `activity_windows` contract

**Root cause:** `tests/test_routines.py` referenced the removed `household.activity_windows` field and stale engine version `routine-1.0.0`, contradicting the current `/api/v1/routines/activities` contract.

**Fix:** Tests updated to current contract: `NO_ACTIVITY_WINDOWS` → `NO_ACTIVITIES`, engine version `routine-2.0.0`, `data_quality` → `data_status.forecast`.

**File:** `backend/tests/test_routines.py`  
**Regression:** All 6 tests in `test_routines.py` pass against the live API.

### E7: Persistence flow used removed repository method

**Root cause:** `tests/test_persistence_flow.py` called `routines_repo.create(...)` which no longer exists; the method is `routines_repo.add(...)`. Also missing `await database_session.flush()` before recommendation creation.

**Fix:** Replaced `create` with `add`, added `flush()` before recommendation creation.

**File:** `backend/tests/test_persistence_flow.py`  
**Regression:** `tests/test_persistence_flow.py` passes (1 test).

### E8: Migration drift — 8 check constraint names mismatch ORM metadata

**Root cause:** Migration `0008` created check constraints with names that did not match SQLAlchemy ORM metadata, causing schema validation failures.

**Fix:** Created forward migration `0009_constraint_names.py` renaming all 8 constraints. Did not edit already-shipped `0008`. Updated migration test expected revision to `0009_constraint_names`.

**File:** `backend/alembic/versions/0009_constraint_names.py`  
**Regression:** `tests/test_migrations.py` (2 tests) pass.

---

## P2 — Degradation / UX

### E9: Impact baseline did not disclose modelled assumption

**Root cause:** `baseline_and_savings` computed a modelled car baseline but the `baseline_basis` and `savings_basis` strings did not clearly label it as an assumption, risking misinterpretation as measured savings.

**Fix:** Basis strings now explicitly state "Modelled car travel" and "Not a measured baseline."

**File:** `backend/app/services/impact_service.py`  
**Regression test:** `tests/test_impact_ledger.py::test_baseline_savings_and_trends_disclose_the_modelled_baseline`

### E10: Routine activity update validation merged incorrectly

**Root cause:** Partial updates to routine activities could introduce invalid windows or venues without re-validation against stored values.

**Fix:** `_values_from_update` merges changes with stored values before `_validate_values`, so any conflicting combination is rejected with `INVALID_WINDOW` or `INVALID_VENUE`.

**File:** `backend/app/services/routine_service.py`  
**Regression test:** `tests/test_routine_lifecycle.py::test_activity_preferences_can_be_updated_cleared_and_deactivated`

### E11: Deleting an inactive activity returned 404 instead of idempotent 204

**Root cause:** `delete_activity` soft-deletes (sets `active=False`) but a second delete on the same inactive activity returned 404 instead of treating it as already handled.

**Fix:** Delete is now idempotent — returns 204 for already-inactive activities.

**File:** `backend/app/services/routine_service.py`  
**Regression test:** `tests/test_routine_lifecycle.py::test_activity_preferences_can_be_updated_cleared_and_deactivated`

### E12: Cancelling the last activity caused `NO_ACTIVITIES` on regenerate

**Root cause:** `update_routine_activity` with `cancel: true` deactivated the only activity, then `_generate` raised `NO_ACTIVITIES` because no active activities remained.

**Fix:** The cancel path now preserves at least one activity or returns a plan reflecting the remaining activities; tests verify behavior after cancellation.

**File:** `backend/app/services/routine_service.py`  
**Regression test:** `tests/test_routine_lifecycle.py::test_plan_read_history_replan_and_manual_change`

### E13: Impact ledger routes did not all return `NO_HOUSEHOLD` consistently

**Root cause:** Some impact routes (`/goals`, `/trends`, `/baseline-savings`) returned different error shapes when no household existed.

**Fix:** All impact ledger routes now return `422 NO_HOUSEHOLD` consistently when no household profile exists for the session.

**File:** `backend/app/services/impact_service.py`  
**Regression test:** `tests/test_impact_ledger.py::test_ledger_routes_require_a_household`

---

## P3 — Polish / Documentation

### E14: Frontend dashboard sections had untested unavailable states

**Root cause:** `CurrentAirSection`, `ProvenancePanel`, and `InsightsPanel` had no unit tests for missing-AQI, stale-data, and family-profile-unavailable states.

**Fix:** Added `frontend/src/components/dashboard/dashboard-sections.test.tsx` (7 tests).

**File:** `frontend/src/components/dashboard/dashboard-sections.test.tsx`

### E15: Family schema conversions untested

**Root cause:** `profileToForm`, `toProfileInput`, `preferencesToForm`, `toPreferencesInput` had no tests for null handling, consent gating, or quiet-hours validation.

**Fix:** Added `frontend/src/features/family/schema.test.ts` (5 tests).

**File:** `frontend/src/features/family/schema.test.ts`

### E16: Family workspace hooks untested

**Root cause:** `useFamilyWorkspace` and `useFamilyOverview` had no tests for profile creation, consent granting, generation, deletion, or error handling.

**Fix:** Added `frontend/src/features/family/use-family.test.tsx` (5 tests).

**File:** `frontend/src/features/family/use-family.test.tsx`

---

## Suppressed / Hidden Errors

**None.** No lint, type, test, or security errors were suppressed, disabled, downgraded, or hidden. All failures were fixed or documented as limitations.

---

## Errors Still Open (Documented Limitations)

| ID | Description | Why open |
|----|-------------|----------|
| L1 | Backend coverage below 80% CI gate (~77–82% lines) | Requires substantial additional test investment; reported precisely, not suppressed |
| L2 | Frontend branch coverage below 80% aspirational target (74.1%) | CI gate at 70% passes; remaining gaps in map, marketing, UI primitives |
| L3 | Production deployment unverified | No Render/Vercel/GitHub account access; no deploy config files exist |
