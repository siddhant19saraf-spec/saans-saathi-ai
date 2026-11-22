# SAANS SAATHI AI — Final Test Report

**Audit date:** 2026-11-21  
**Scope:** All backend and frontend tests, coverage, lint, typecheck, build, security

---

## Backend Test Results

### Full DB-Backed Suite (verified)

| Metric | Result |
|--------|--------|
| Tests passed | 264 |
| Tests failed | 0 |
| Tests skipped | 0 (82 previously skipped DB tests now run) |
| Duration | ~6 minutes |
| DB | `saans_test` (PostgreSQL 16.15, isolated) |

### New Regression Tests (all passing)

| File | Tests |
|------|-------|
| `tests/test_routine_lifecycle.py` | 9 |
| `tests/test_impact_ledger.py` | 5 |
| `tests/test_household_edges.py` | 2 |
| `tests/test_tool_executor.py` | 6+ |
| `tests/test_copilot.py` | FactPack/no-coords/privacy + validation flag |
| `tests/test_routines.py` | 6 |
| `tests/test_migrations.py` | 2 |
| `tests/test_persistence_flow.py` | 1 |

### Coverage (pytest --cov=app)

Last verified full DB run: **77.53% lines** vs. 80% `fail_under` gate.

Per-file coverage highlights:

| File | Lines | Branch | Status |
|------|-------|--------|--------|
| `app/api/v1/air.py` | 98% | 100% | ✓ |
| `app/api/v1/copilot.py` | 82% | 100% | ~ |
| `app/api/v1/ecoroute.py` | 90% | 100% | ~ |
| `app/api/v1/family.py` | 98% | 100% | ✓ |
| `app/api/v1/health.py` | 100% | 100% | ✓ |
| `app/api/v1/household.py` | 92% | 100% | ~ |
| `app/api/v1/impact.py` | 83% | 100% | ~ |
| `app/api/v1/indoor.py` | 78% | 100% | ~ |
| `app/api/v1/locations.py` | 94% | 100% | ~ |
| `app/api/v1/routines.py` | 73% | 100% | ~ |
| `app/api/v1/sessions.py` | 87% | 100% | ~ |
| `app/core/config.py` | 88% | 92% | ~ |
| `app/core/database.py` | 94% | 92% | ~ |
| `app/core/exceptions.py` | 99% | 88% | ✓ |
| `app/core/logging.py` | 94% | 83% | ~ |
| `app/core/loop.py` | 80% | 50% | ~ |
| `app/core/middleware.py` | 87% | 72% | ~ |
| `app/core/rate_limit.py` | 71% | 75% | ~ |
| `app/core/security.py` | 84% | 67% | ~ |
| `app/domain/aqi.py` | 97% | 94% | ✓ |
| `app/domain/carbon.py` | 97% | 97% | ✓ |
| `app/domain/exposure.py` | 78% | 50% | ~ |
| `app/domain/factors.py` | 88% | 93% | ~ |
| `app/domain/family_rules.py` | 84% | 86% | ~ |
| `app/domain/indoor.py` | 86% | 50% | ~ |
| `app/domain/indoor_shield.py` | 89% | 83% | ~ |
| `app/domain/routine.py` | 90% | 83% | ✓ |
| `app/integrations/ai/fallback.py` | 81% | 59% | ~ |
| `app/integrations/ai/gemini.py` | 36% | 100% | Low |
| `app/integrations/ai/tool_executor.py` | 39% | 78% | Low |
| `app/integrations/ai/validation.py` | 83% | 72% | ~ |
| `app/integrations/air_quality/cpcb.py` | 90% | 100% | ✓ |
| `app/integrations/air_quality/open_meteo.py` | 65% | 78% | ~ |
| `app/integrations/air_quality/openaq.py` | 77% | 69% | ~ |
| `app/integrations/geocoding/client.py` | 84% | 77% | ~ |
| `app/main.py` | 71% | 92% | ~ |
| `app/models/ecoroute.py` | 97% | 50% | ✓ |
| `app/repositories/air.py` | 91% | 50% | ~ |
| `app/repositories/conversations.py` | 79% | 100% | ~ |
| `app/repositories/ecoroute.py` | 64% | 94% | Low |
| `app/repositories/households.py` | 81% | 75% | ~ |
| `app/repositories/impact.py` | 94% | 100% | ✓ |
| `app/repositories/indoor.py` | 78% | 75% | ~ |
| `app/repositories/profiles.py` | 78% | 100% | ~ |
| `app/repositories/recommendations.py` | 94% | 100% | ✓ |
| `app/repositories/routines.py` | 78% | 75% | ~ |
| `app/schemas/common.py` | 0% | — | Uncovered |
| `app/schemas/copilot.py` | 90% | 86% | ~ |
| `app/schemas/ecoroute.py` | 92% | 83% | ~ |
| `app/schemas/household.py` | 92% | 69% | ~ |
| `app/schemas/indoor.py` | 95% | 55% | ✓ |
| `app/schemas/routines.py` | 85% | 71% | ~ |
| `app/services/ai_budget.py` | 81% | 100% | ~ |
| `app/services/air_quality_service.py` | 72% | 80% | ~ |
| `app/services/copilot_service.py` | 77% | 74% | ~ |
| `app/services/ecoroute_service.py` | 85% | 89% | ~ |
| `app/services/family_service.py` | 63% | 80% | Low |
| `app/services/health_service.py` | 88% | 75% | ~ |
| `app/services/household_service.py` | 64% | 95% | Low |
| `app/services/impact_service.py` | 36% | — | Low |
| `app/services/indoor_service.py` | 93% | 81% | ✓ |
| `app/services/indoor_shield_service.py` | 49% | 85% | Low |
| `app/services/location_service.py` | 94% | 100% | ✓ |
| `app/services/routine_service.py` | 37% | 88% | Low |
| `app/services/session_service.py` | 91% | 50% | ~ |
| `app/utils/cache.py` | 81% | 67% | ~ |

**Low coverage files (<60%):** `gemini.py`, `tool_executor.py`, `impact_service.py`, `indoor_shield_service.py`, `routine_service.py`, `ecoroute_repo.py`, `household_service.py`, `family_service.py`

**Uncovered:** `app/schemas/common.py` (14 statements, 0%)

**90% target:** Not reachable without substantial additional test investment; measured precisely and reported.

---

## Lint / Typecheck / Security (Backend)

| Tool | Command | Result |
|------|---------|--------|
| Ruff | `ruff check app` | Clean |
| Black | `black app` | Clean |
| MyPy | `mypy app` (107 files) | Clean |
| Bandit | `bandit` | 0 findings |
| pip-audit | `pip-audit` | Clean |
| Secret scan | `gitleaks` / secret scan | Only expected placeholders |

---

## Frontend Test Results

### Full Test Suite (verified)

| Metric | Result |
|--------|--------|
| Tests passed | All (baseline 49 + 36+ added) |
| Tests failed | 0 |
| Duration | < 2 minutes |

### Coverage (vitest run --coverage)

| Metric | Measured | CI Gate | Aspirational Target |
|--------|----------|---------|---------------------|
| Statements | 86.9% | 70% ✓ | 80% |
| Branches | 74.1% | 70% ✓ | 80% |
| Functions | 87.8% | 70% ✓ | 80% |
| Lines | 87.1% | 70% ✓ | 80% |

All CI gates pass. The 80% aspirational target is not fully met for branches; remaining gaps in map view/canvas, marketing components, and UI primitives.

### New Frontend Tests (all passing)

| File | Tests | Purpose |
|------|-------|---------|
| `navigation-shell.test.tsx` | 14 | CommandSearch, LocationSwitcher, Notifications, UserMenu, Breadcrumbs, Layout |
| `map-view.test.tsx` | 7 | MapView, MapCanvas with Leaflet mocking |
| `routes.test.tsx` | 15 | All 10 app routes + marketing + error/loading/404 |
| `dashboard-sections.test.tsx` | 7 | CurrentAirSection, ProvenancePanel, InsightsPanel |
| `family/schema.test.ts` | 5 | Profile/preferences schema validation |
| `family/use-family.test.tsx` | 5 | Workspace hooks (save, generate, delete, end session) |
| `storage.test.ts` | 9 | Storage read/write/remove/hydration edge cases |
| `session.test.ts` | 6 | Session storage round-trip, expiry, stability |
| `location-context.test.tsx` | 6 | Location add/remove/activate, MAX 8 cap |
| `nav-config.test.ts` | 3 | Route finding, breadcrumb trail |

### Frontend Lint / Typecheck / Build

| Tool | Command | Result |
|------|---------|--------|
| ESLint | `npm run lint` | Clean |
| TypeScript | `npm run typecheck` (tsc --noEmit) | Clean |
| Vitest | `npm test` | All passing |
| Build | `npm run build` (12 routes) | Clean |

---

## CI Quality Gates (`.github/workflows/quality-checks.yml`)

| Gate | Command | Result |
|------|---------|--------|
| Backend tests | `uv run pytest --cov` | Coverage gate not yet cleared (77.53% vs 80%) |
| Backend audit | `uv run pip-audit` | Clean |
| Backend lint | Bandit | 0 findings |
| Secret scan | gitleaks | Only placeholders |
| Repo size | `scripts/check-repo-size.sh 10` | Tracked ~3 MB ✓ |
| Frontend tests | `npm run test:coverage` | All gates pass ✓ |
| Frontend lint | `npm run lint` | Clean ✓ |
| Frontend typecheck | `npm run typecheck` | Clean ✓ |
| Frontend build | `npm run build` | 12 routes, clean ✓ |

---

## Test Environment

- **Backend:** Python 3.13.14, pytest 9.2.0, pytest-asyncio 1.5.0, SQLAlchemy async, psycopg
- **Frontend:** Node.js, Next.js 16.4.6, React 19.3.1, Vitest 5.1.1, TypeScript 5.9.3, jsdom
- **Database:** PostgreSQL 16.15 local; `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/saans_test`
- **OS:** Windows (PowerShell); `asyncio.WindowsSelectorEventLoopPolicy` for psycopg async
