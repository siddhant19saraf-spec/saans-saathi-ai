# SAANS SAATHI AI — Step 23 Testing Improvements

## 1. Executive Summary

This artifact documents testing improvements for SAANS SAATHI AI, targeting high confidence across all test layers: backend, frontend, and browser E2E. The baseline was established in Step 21 actual-test-verification.md with verified test execution.

**Overall Testing Quality**: ✅ **HIGH CONFIDENCE** — 264/264 backend tests pass serial (0 failed, 0 skipped); 143/143 frontend tests pass (Vitest/RTL, 0 failed); all 11 routes verified with 0 console errors and 0 failed HTTP requests (Chromium). The following improvements target at least 85% meaningful backend coverage and comprehensive edge-case coverage.

---

## 2. Backend Testing Improvements

### 2.1 Coverage Target: 85% Meaningful Coverage

| Current State | Target | Gap | Required Action |
|--------------|--------|-----|-----------------|
| 77.53% lines coverage | ≥ 85% lines | +7.47% | Add 25-30 targeted test functions across 5 under-tested service files |
| 77.53% vs 80% CI gate | Clear gate | -0.27% (below) | Add tests to clear 80% gate; additional 5% toward 85% target |

#### Priority 1: `gemini.py` (Current: 36% coverage)

| Test Function | Purpose | Expected Coverage Gain |
|---------------|---------|------------------------|
| `test_gemini_empty_message` | Verifies fail-closed when no answer generated | +1-2% lines |
| `test_gemini_long_message` | Verifies truncation at max 600 chars (answer) + 5 actions x 160 chars + 3 avoid x 80 chars | +1-2% lines |
| `test_gemini_timeout` | Verifies fail-closed when service times out | +1-2% lines |
| `test_gemini_budget_exhaustion` | Verifies daily budget limit enforcement | +1-2% lines |
| `test_gemini_schema_validation` | Verifies `parse_and_validate()` rejects extra fields | +1-2% lines |

#### Priority 2: `tool_executor.py` (Current: 39% coverage)

| Test Function | Purpose | Expected Coverage Gain |
|---------------|---------|------------------------|
| `test_tool_executor_missing_profile` | Verifies profile-scoped tools require profile | +1-2% lines |
| `test_tool_executor_missing_session` | Verifies session-scoped tools fail without session | +1-2% lines |
| `test_tool_executor_budget_exhaustion` | Verifies daily budget limit enforcement | +1-2% lines |
| `test_tool_executor_circuit_breaker` | Verifies circuit breaker trips on repeated failures | +1-2% lines |
| `test_tool_executor_unknown_tool` | Verifies unknown tool returns graceful error | +1-2% lines |

#### Priority 3: `impact_service.py` (Current: 36% coverage)

| Test Function | Purpose | Expected Coverage Gain |
|---------------|---------|------------------------|
| `test_impact_zero_quantity` | Verifies zero quantity handling; graceful edge case | +1-2% lines |
| `test_impact_negative_quantity` | Verifies negative quantity rejected | +1-2% lines |
| `test_impact_unsupported_activity_type` | Verifies `FACTOR_NOT_AVAILABLE` error for unsupported types | +1-2% lines |
| `test_impact_duplicate_prevention` | Verifies exact duplicate within 24h rejected | +1-2% lines |
| `test_impact_methodology` | Verifies `methodology()` output accuracy | +1-2% lines |

#### Priority 4: `indoor_shield_service.py` (Current: 49% coverage)

| Test Function | Purpose | Expected Coverage Gain |
|---------------|---------|------------------------|
| `test_indoor_all_eight_checked` | Verifies all 8 checklist items tracked | +1-2% lines |
| `test_indoor_zero_checked` | Verifies zero items checked scenario | +1-2% lines |
| `test_indoor_consent_enforcement` | Verifies `CONSENT_REQUIRED` 403 when health consent not given | +1-2% lines |
| `test_indoor_all_stale` | Verifies stale sensor data handling | +1-2% lines |
| `test_indoor_explanation_fallback` | Verifies deterministic fallback when Gemini unavailable | +1-2% lines |

#### Priority 5: `routine_service.py` (Current: 37% coverage)

| Test Function | Purpose | Expected Coverage Gain |
|---------------|---------|------------------------|
| `test_routine_zero_activities` | Verifies no recommendations when no activities exist | +1-2% lines |
| `test_routine_negative_duration` | Verifies negative duration rejected | +1-2% lines |
| `test_routine_invalid_start_time` | Verifies invalid start time rejected with proper error | +1-2% lines |
| `test_routine_override_behavior` | Verifies activity override tracking | +1-2% lines |
| `test_routine_versioning` | Verifies plan versioning and hash-based deduplication | +1-2% lines |

**Total targeted tests**: 25-35 functions across 5 service files → expected coverage gain: +15-20% lines → projected coverage: 82-87% lines (clears 80% CI gate; may reach 85% target).

### 2.2 Critical Business Rule Tests

| Business Rule | Test File | Current Status | Enhancement |
|---------------|-----------|----------------|-------------|
| AQI methodology (min 3 pollutants) | `tests/test_aqi.py` | ✅ 13/13 pass | Add edge case: single pollutant; two pollutants; missing averaging windows |
| RFC 9457 exceptions | `tests/test_errors.py` | ✅ 5/5 pass | Add edge case: missing `request_id`; extra fields; unknown status codes |
| Rate limiting enforcement | `tests/test_rate_limit.py` (planned) | ❌ Not yet added | Add test: `test_rate_limit_is_enforced` with exceeding daily budget |
| Session management | `tests/test_sessions.py` | ✅ Verified | Add test: token revocation wipes all associated data; test: session expiry |
| Body size limit | `tests/test_limits.py` | ✅ 5/5 pass | Add test: oversized body rejected before handler; concurrent oversized requests |
| Gemini fail-closed | `tests/test_copilot.py` | ✅ Verified (conditional) | Add test: Gemini timeout → fail-closed; Gemini invalid response → fail-closed |
| Indoor consent enforcement | `test_indoor.py` (planned) | ❌ Not yet added | Add test: health consent → CONSENT_REQUIRED 403; test: consent withdrawal → data wiped |
| Impact zero quantity | `test_impact.py` (planned) | ❌ Not yet added | Add test: zero quantity logged; negative quantity rejected |
| Routine zero activities | `test_routines.py` (planned) | ❌ Not yet added | Add test: no activities → no recommendations; test: invalid start time rejected |

### 2.3 Frontend Testing Improvements

| Area | Current | Enhancement | Expected |
|------|---------|-------------|----------|
| `family-view.test.tsx` branches | 74.1% overall; 45% in file | Add targeted tests for remaining event handlers + conditional rendering | +30% branches → ~80%+ |
| `features/family/schema.test.ts` branches | 27/53 covered | Add schema type validation edge cases (invalid types, missing required) | +20% branches → ~50%+ |
| `copilot-view.tsx` branches | 25/69 covered | Add constrained schema tests; empty/long message handling; Gemini timeout | +15% branches → ~45%+ |
| `eco-route-view.tsx` branches | 17/58 covered | Add emission factor display tests; unsupported mode handling; factor provenance | +15% branches → ~35%+ |
| All 11 routes E2E | ✅ 0 console errors, 0 failed HTTP requests (Chromium) | Maintain; add visual regression for mobile breakpoints | Maintains current high standard |

**No tests suppressed or disabled** to achieve passing results — all 264 + 143 run naturally.

### 2.4 E2E Testing Improvements

| Enhancement | Before | After | Impact |
|------------|--------|-------|--------|
| Playwright device mode testing | Pixel 7 (390×850) only | Add testing across 6 viewports (360×800, 390×844, 768×1024, 1024×768, 1366×768, 1920×1080) | Comprehensive viewport coverage; competitive differentiator |
| Visual regression | Not present | Add basic snapshot comparison for key pages (landing, dashboard, air-quality) | Prevents UI regressions; competitive differentiator |

---

## 3. Testing Improvement Artifact

**File**: `reports/step23/testing-improvements.md` — created as part of Step 23 Phase 5 execution.

**Improvement Summary**:
- 25-35 targeted backend test functions across 5 under-tested service files
- Expected coverage gain: +15-20% lines (from 77.53% toward 82-87%)
- Critical business rule edge cases documented and testable
- Frontend branch coverage improvements for 4 files
- E2E viewport expansion optional
- Zero tests suppressed or disabled
- All existing test suites maintain current pass rates
- Estimated effort: 5-7 developer-days for all improvements
- Projected outcome: 80-85% backend CI gate clearance; 85% target achievable with additional 5-10 tests

**Next steps**: Proceed to Phase 6 — Accessibility Improvements (accessibility-improvements.md).