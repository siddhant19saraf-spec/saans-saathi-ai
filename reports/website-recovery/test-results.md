# Test Results — SAANS SAATHI AI Website Recovery

**Status:** COMPLETE — all suites measured  
**Date:** Mon Nov 23 2026  
**Engineer:** Principal Full-Stack / FastAPI / Next.js

## Backend (pytest)

Run with `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/saans_test`.

| Metric | Value |
|---|---|
| Command | `pytest --cov=app --cov-report=term -q` |
| Duration | 7m39s (459.57s) |
| Passed | **280** |
| Failed | **0** |
| Skipped | 0 (with DB set) |
| Coverage | TOTAL 78.86% (8287 statements, 320 missing) |
| Coverage gate | `FAIL Required test coverage of 80.0% not reached` |

The coverage gate failure is **pre-existing** on the committed tree (baseline 77.53%, this session 78.86%). It was documented, not suppressed. Per constraints: failing tests were not removed and assertions not weakened.

Coverage file: `recovery_pytest_full.log`

## Frontend unit tests (Vitest)

| Metric | Value |
|---|---|
| Command | `npx vitest run` |
| Duration | 14.49s |
| Passed | **149** |
| Failed | **0** |
| Test files | 28 |
| Environment | jsdom |

Coverage file: `recovery_vitest.log`

## E2E (Playwright, desktop Chromium)

Against production build (`npm run start`, port 3001).

| Suite | Tests | Passed | Failed |
|---|---|---|---|
| `e2e/smoke.spec.ts` (pre-existing) | 2 | 2 | 0 |
| `e2e/recovery.spec.ts` (new) | 13 | 13 | 0 |
| **Total** | **15** | **15** | **0** |

`recovery.spec.ts` asserts per-route hydration (exact h1 visible in `<main>`, shell revealed, loading fallback removed, React >50 elements, skeleton replaced, >150 chars main content, zero console/page errors), seven modules in navigation, and client-side module navigation.

Coverage file: `recovery_e2e_final2.log`

## Lint / type / format

| Tool | Scope | Result |
|---|---|---|
| Ruff | backend (`.`) | clean (exit 0) |
| Black | backend (`.`) | clean (exit 0) |
| MyPy | backend `app` | clean (exit 0) |
| Bandit | backend `app` (`-c pyproject.toml -r app`) | exit 0 |
| ESLint | frontend (`.`) | clean (exit 0) |
| `tsc --noEmit` | frontend | clean (exit 0) |

## Build

| Command | Result |
|---|---|
| `npm run build` (Next.js 16.4.6 Turbopack) | **PASS** — 11 static routes + `_not-found` |

## Historical comparison (superseded figures)

| Metric | Prior baseline | This session | Status |
|---|---|---|---|
| Backend tests | 264 | 280 | ✅ improved |
| Backend tests failed | 0 | 0 | ✅ same |
| Frontend tests | 143 | 149 | ✅ improved |
| Coverage | 77.53% | 78.86% | ⚠️ still <80% gate (pre-existing) |

## Pre-existing fixes on the committed tree (not caused by this session)

- Ruff W292 in `alembic/versions/0008_ecoroute_impact.py`
- Ruff I001 in `tests/test_copilot.py`
- Ruff F841 in `tests/test_routine_lifecycle.py` (dropped only the unused `activity =` assignment)
- Black reformatting of 5 files

None of these are part of the website-recovery task; they were already failing on HEAD `0a22cc4`.

## Test artifacts

- `frontend/e2e/recovery.spec.ts` — new E2E verification suite (added, not modifying existing tests)
- `test-results/` — Playwright traces/screenshots on failure (none in final run)

## Conclusion

All verification suites pass: 280/280 backend, 149/149 frontend unit, 15/15 E2E, lint/format/type clean, build passes. The only gate not met is the pre-existing 80% coverage threshold (78.86%), documented and not suppressed.
