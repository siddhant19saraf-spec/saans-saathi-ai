# SAANS SAATHI AI — Backend Coverage Improvement Plan

## Current State

| Metric | Value | Target | Gap |
|--------|-------|--------|-----|
| Backend line coverage | 77.53% | 80% CI gate | 2.47 percentage points |
| Under-tested service files | 5 files | — | — |
| Total backend test functions | 264 | — | — |
| Tests passing (serial) | 264 | 0 failed | ✅ |

## Under-Tested Service Files

| File | Current Coverage | Test File(s) | Gap |
|------|-----------------|--------------|-----|
| `app/integrations/ai/gemini.py` | 36% | `tests/test_copilot.py`, `tests/test_open_meteo.py` | ~64% uncovered |
| `app/integrations/tool_executor.py` | 39% | `tests/test_tool_executor.py` | ~61% uncovered |
| `app/services/impact_service.py` | 36% | `tests/test_impact.py`, `tests/test_impact_ledger.py` | ~64% uncovered |
| `app/services/indoor_shield_service.py` | 49% | `tests/test_indoor.py`, `tests/test_indoor_shield.py` | ~51% uncovered |
| `app/services/routine_service.py` | 37% | `tests/test_routines.py`, `tests/test_routine_engine.py`, `tests/test_routine_lifecycle.py`, `tests/test_step10.py` | ~63% uncovered |

## Coverage Improvement Strategy

### Principle: Add Targeted Tests Only
- Do not rewrite working modules.
- Add tests that exercise currently unguarded code paths.
- Focus on error handling, edge cases, and validation boundaries.
- Maintain serial test execution (concurrent runs cause connection exhaustion).

### File-by-File Improvement Plan

### 1. `app/integrations/ai/gemini.py` (36% → 80%+)
**Current tests**: `test_copilot.py` (basic Gemini interaction), `test_open_meteo.py` (Open-Meteo provider)

**Missing test categories**:
- Empty message handling → Gemini should return "no answer generated here"
- Very long message → character limit enforcement (0/800 characters)
- Gemini timeout → fail-closed behavior (no answer when service unavailable)
- Provider budget exhaustion → daily request budget enforcement (300 requests)
- Invalid JSON response → parse error handling
- Schema validation failure → `parse_and_validate()` rejection
- Deterministic fallback when Gemini unavailable → confirm recommendations still functional

**Suggested test additions** (each ~1-3 test functions):
```python
# test_gemini_empty_message.py
async def test_gemini_empty_message_returns_no_answer():
    """Empty message should produce no answer — fail closed."""
    ...

# test_gemini_timeout_fallback.py
async def test_gemini_timeout_uses_deterministic_fallback():
    """When Gemini times out, deterministic recommendations are used."""
    ...

# test_gemini_schema_validation.py
async def test_gemini_invalid_json_schema_rejected():
    """Malformed Gemini JSON output is rejected via parse_and_validate()."""
    ...
```

### 2. `app/integrations/tool_executor.py` (39% → 80%+)
**Current tests**: `tests/test_tool_executor.py` (6 tests: unknown tool, air-quality requires configured service, without coordinates, profile-scoped, journey_id validation, profile-scoped tools require profile)

**Missing test categories**:
- Tool execution with missing profile → unauthorized response
- Tool execution with missing session → error response
- Invalid argument types → schema validation rejection
- Tool budget exhaustion → daily call budget enforcement
- Circuit breaker behavior after consecutive failures
- Specific tool: get_air_quality with various coordinate formats
- Specific tool: compare_transport_options with invalid journey

**Suggested test additions**:
```python
# test_tool_executor_missing_profile.py
async def test_tool_executor_missing_profile_returns_unauthorized():
    """Tool execution without profile returns unauthorized."""
    ...

# test_tool_executor_budget.py
async def test_tool_executor_daily_budget_enforcement():
    """Tool budget exceeds daily limit — rejected."""
    ...
```

### 3. `app/services/impact_service.py` (36% → 80%+)
**Current tests**: `tests/test_impact.py`, `tests/test_impact_ledger.py`

**Missing test categories**:
- Activity logging with zero quantity → handled gracefully
- Activity logging with negative quantity → rejected
- Unsupported activity types → FACTOR_NOT_AVAILABLE error
- Emission factor provenance retrieval → source_title, source_url, version, retrieved_on displayed
- Baseline assumption disclosure → "Amounts are the quantities you entered, not savings"
- Goals/trends computation with empty log → handled
- Factor provenance format validation → _RESPONSE_SCHEMA compliance

**Suggested test additions**:
```python
# test_impact_unsupported_activity.py
async def test_impact_unsupported_activity_type_rejected():
    """Unsupported activity type returns FACTOR_NOT_AVAILABLE."""
    ...
```

### 4. `app/services/indoor_shield_service.py` (49% → 80%+)
**Current tests**: `tests/test_indoor.py`, `tests/test_indoor_shield.py`

**Missing test categories**:
- All 8 shelter checklist items checked → progress = 8/8
- Zero items checked → progress = 0/8
- Missing health consent → CONSENT_REQUIRED error (403)
- Invalid shelter type → rejected
- Recommendation generation after assessment → grounded in deterministic rules
- Sensor data claims → explicitly not claimed ("no indoor sensor data is claimed")
- Ventilation guidance with various combinations

**Suggested test additions**:
```python
# test_indoor_shield_full_checklist.py
async def test_indoor_shield_all_items_checked():
    """All 8 checklist items checked → progress 8/8."""
    ...
```

### 5. `app/services/routine_service.py` (37% → 80%+)
**Current tests**: `tests/test_routines.py`, `tests/test_routine_engine.py`, `tests/test_routine_lifecycle.py`, `tests/test_step10.py`

**Missing test categories**:
- Activity add with invalid start time → validation error
- Activity add with duration = 0 → handled
- Activity add with negative duration → rejected
- Routine generation with no activities → no recommendations
- Routine override behavior → versioned plans, overrides, replanning
- Timezone-aware activity start times → correct offset handling
- Flexible vs. fixed activity windows → different behavior
- Duration flexibility enforcement → max/min duration constraints
- Activity removal → updated plan reflects removal

**Suggested test additions**:
```python
# test_routine_service_invalid_activity.py
async def test_routine_service_invalid_start_time_rejected():
    """Activity with invalid start time returns 422."""
    ...
```

## Implementation Plan

### Step 1: Add Tests (estimated: 1-2 days)
Add 15-25 new test functions across the 5 under-tested service files, focused on:
- Error/edge-case handling (primary gap)
- Boundary validation
- Fail-closed behavior
- Provider budget/circuit breaker enforcement

### Step 2: Verify Coverage (estimated: < 1 day)
Run `uv run pytest --cov` serially and verify coverage reaches 80%+ lines.
If exact 80% is not reached on first attempt, add 5-8 more targeted tests.

### Step 3: Regression Test (estimated: < 1 day)
Run full suite: `uv run pytest --cov` — verify 264+ new/existing tests pass, 0 failures.

### Step 4: Document (estimated: < 0.5 day)
Update `reports/step18/optimization-log.md` and `reports/step18/technical-scorecard.md` with new coverage figures.

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Coverage not reaching 80% after initial test additions | Medium | Medium | Add 5-8 more targeted tests; focus on error/edge-case paths |
| Regression introduced by new tests | Low | High | All new tests must pass with `uv run pytest --cov`; existing 264 tests must remain 0 failures |
| Serial run connection exhaustion during coverage run | Medium | High | Ensure no orphaned pytest processes; use `TEST_DATABASE_URL`; limit to one coverage run at a time |
| Tests become stale with code changes | Low | Medium | Add tests near `if __name__ == \"__main__\"` guard; keep test file alongside source |

## Expected Outcome

After improvement:
- **Backend coverage**: 80%+ lines (CI gate cleared)
- **No new defects**: All 264+ tests pass serially
- **No regressions**: Existing behavior preserved
- **Documentation updated**: Coverage figures reflected in scorecard and submission readiness

**Note**: This improvement is optional for CONDITIONAL GO. The current 77.53% is documented as a known non-blocking limitation. However, clearing the CI gate strengthens the submission.