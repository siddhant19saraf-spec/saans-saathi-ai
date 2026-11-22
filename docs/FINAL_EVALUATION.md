# SAANS SAATHI AI — Final Evaluation Report

**Evaluator role:** Independent hackathon evaluator, principal software architect, AI researcher, product strategist, security engineer, UX reviewer  
**Evaluation date:** 2026-11-22  
**Project:** SAANS SAATHI AI  
**Framework:** 100-point evaluation (internal weights — not official hackathon scoring)

---

## A. Overall Score

| Category | Weight | Score | Weighted |
|----------|--------|-------|----------|
| Code Quality | 20 | 78/100 | 15.6 |
| Security | 20 | 85/100 | 17.0 |
| Efficiency | 15 | 82/100 | 12.3 |
| Testing | 15 | 72/100 | 10.8 |
| Accessibility | 10 | 68/100 | 6.8 |
| Problem Alignment | 20 | 88/100 | 17.6 |
| **Total** | **100** | — | **70.1/100** |

**Internal score: 70.1/100**

This is a solid, well-engineered project with genuine differentiators, but it is not competition-leading. The score reflects strong security and problem alignment, moderated by testing gaps (backend coverage below CI gate), accessibility gaps (no automated a11y testing), and some code-quality concerns (low-coverage service files).

---

## B. Category-by-Category Evaluation

### A. Code Quality — 78/100

**Strengths:**

- **Clean separation of concerns:** Domain logic (`app/domain/*`) is pure, testable, and separate from services (`app/services/*`) and API routes (`app/api/v1/*`). This is evident in `routine.py`, `indoor_shield.py`, `carbon.py`, `exposure.py`, `aqi.py` — all pure functions with no framework dependencies.
- **Deterministic engines:** SmartRoutine (`routine-2.0.0`), IndoorShield (`indoor-shield-1.0.0`), and carbon estimation are all pure functions over validated inputs. Identical inputs produce identical outputs — critical for trust in environmental recommendations.
- **Versioned engines:** `ENGINE_VERSION` stored with every plan; `STALE_ENGINE_VERSION` error prevents serving outdated plans.
- **Explicit error taxonomy:** RFC 9457 problem responses (`application/problem+json`) with stable `code` strings. Client-facing payloads never contain stack traces or SQL.
- **No raw SQL:** SQLAlchemy ORM with parameterized queries throughout.
- **Fail-closed AI:** Model output validated against FactPack; rejected output never shown; deterministic fallback always available.

**Weaknesses:**

- **Low-coverage service files:** `gemini.py` (36% lines), `tool_executor.py` (39%), `impact_service.py` (36%), `indoor_shield_service.py` (49%), `routine_service.py` (37%). These are the most business-critical files and have the least test coverage.
- **Uncovered schema module:** `app/schemas/common.py` — 14 statements, 0% coverage.
- **Backend coverage below CI gate:** 77.53% lines vs. 80% `fail_under`. The CI would fail on this.
- **Some inline complexity:** `copilot_service.py` `_build_fact_pack` is ~200 lines doing multiple service integrations; could benefit from decomposition.
- **Character encoding issues:** Several source files contain replacement characters (�) in comments and strings, suggesting encoding problems during file creation/editing.

**Evidence:** `backend/coverage.xml` (line-rate 0.8188 overall, but per-file variance), `backend/app/services/copilot_service.py`, `backend/app/integrations/ai/tool_executor.py`

**Score: 78/100** — Good architecture, but critical files under-tested and encoding issues present.

---

### B. Security — 85/100

**Strengths:**

- **Bearer token authentication:** Opaque tokens with SHA-256 digests stored server-side. Tokens never logged.
- **Session expiry:** `expires_at` validated on read; expired sessions return null.
- **Profile scoping:** All data access filtered by `profile_id` from bearer token; cross-profile access returns 404.
- **Health-data consent:** Health flags require explicit consent; missing consent → 403 `CONSENT_REQUIRED`. Both backend-enforced and frontend-form-validated.
- **CORS:** Wildcard CORS explicitly rejected. `ALLOWED_HOSTS` default is `localhost,127.0.0.1,testserver`; production must set explicitly.
- **Security headers:** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` (backend middleware); `Cache-Control: no-store` on personal endpoints; Next.js sets COOP, Permissions-Policy.
- **Body size limits:** Configured to prevent large-payload abuse.
- **Rate limiting:** Per-session and per-IP limits on write-heavy routes. AI daily budget enforced.
- **No secrets in repo:** Secret scan found only expected placeholders. `.env.example` tracked with dummy values. `.env` not tracked.
- **Fail-closed AI validation:** Model can never inject data — citations rebuilt server-side, fact references validated, numbers grounded, unsafe content stripped.
- **No PII to model:** FactPack explicitly excludes names, coordinates, free-text notes, health conditions.

**Weaknesses:**

- **No penetration testing:** Security verified only via static analysis (Bandit) and dependency scanning (`pip-audit`).
- **Production CORS origins unverified:** Cannot confirm production `ALLOWED_HOSTS`/`FRONTEND_URL` without deploy access.
- **No OAuth/SSO/MFA:** Anonymous session model only — acceptable for MVP but limits enterprise adoption.
- **No production DATABASE_URL:** Required in production but not configured.

**Evidence:** `backend/app/core/middleware.py`, `backend/app/core/config.py`, `backend/app/services/session_service.py`, `backend/app/integrations/ai/validation.py`

**Score: 85/100** — Strong security posture for an MVP, but lacks external validation.

---

### C. Efficiency — 82/100

**Strengths:**

- **Deterministic scheduling:** No LLM used for compute-intensive SmartRoutine scheduling — pure Python function. Massive token and latency savings.
- **Provider caching:** TTLCache (60s memory) for air-quality responses; PostgreSQL snapshot layer.
- **Circuit breakers:** Per-provider circuit breakers prevent cascading failures and wasted calls.
- **Per-provider budgets:** Daily call budgets per provider; exhausted → graceful degradation.
- **AI used only for explanations:** Gemini only rephrases pre-computed plans; never makes scheduling or emission decisions.
- **Pagination:** Impact activities, routine history, and family recommendations all paginated.
- **Frontend code splitting:** Next.js App Router with route-based splitting; `next/dynamic` for map canvas (SSR off).
- **Snapshot caching:** `useSyncExternalStore` with stable references prevents unnecessary re-renders.

**Weaknesses:**

- **No production load testing:** Cannot measure under production traffic.
- **No database query profiling:** EXPLAIN ANALYZE not performed; index strategy not reviewed.
- **No bundle size analysis:** `next-bundle-analyzer` not configured.
- **No Core Web Vitals:** Lighthouse/CRuX not run.
- **Connection pooling:** NullPool for tests; production pool configuration not reviewed.

**Evidence:** `backend/app/services/air_quality_service.py` (TTLCache, CircuitBreaker), `backend/app/domain/routine.py` (pure function), `frontend/next.config.ts`

**Score: 82/100** — Excellent architectural choices for efficiency, but unmeasured in production.

---

### D. Testing — 72/100

**Strengths:**

- **Backend:** 264 tests passing, 0 failed, 0 skipped (82 previously skipped DB tests now run).
- **Frontend:** All tests passing (baseline 49 + 36+ added across navigation, map, routes, dashboard, family, storage, session, location-context).
- **New regression tests:** `test_routine_lifecycle.py` (9), `test_impact_ledger.py` (5), `test_household_edges.py` (2), `test_tool_executor.py` (6+), `test_copilot.py` FactPack/privacy tests.
- **Deterministic test data:** All tests use fabricated fixtures, not real sensor/location data.
- **Isolated test DB:** `saans_test` database; schema rebuilt per session; tables truncated per test.
- **CI gates:** Frontend coverage gates (70%) all pass.

**Weaknesses:**

- **Backend coverage below CI gate:** 77.53% vs 80% `fail_under` — CI would fail.
- **Critical files under-tested:** `gemini.py` (36%), `tool_executor.py` (39%), `impact_service.py` (36%), `indoor_shield_service.py` (49%), `routine_service.py` (37%) — these contain the core business logic.
- **No load/performance tests:** No response-time or throughput assertions.
- **No contract tests:** API contracts documented but not automatically verified against implementations.
- **Frontend branch coverage:** 74.1% vs 80% aspirational target; gaps in map, marketing, UI primitives.
- **No E2E tests:** No end-to-end user journey tests (e.g., Playwright/Cypress).

**Evidence:** `backend/coverage.xml`, `frontend/coverage/lcov.info`, `backend/tests/`

**Score: 72/100** — Good test volume but critical business logic under-covered; CI gate not cleared.

---

### E. Accessibility — 68/100

**Strengths:**

- **Skip link:** `SkipLink` renders first, links to `#main-content`.
- **Landmarks:** `<main id="main-content">`, `aria-label="Primary"` topbar, `aria-label="Breadcrumb"`, `aria-label="Site"` marketing nav.
- **Region labels:** `aria-labelledby` on dashboard sections.
- **Button labels:** All buttons have visible text or `aria-label`.
- **Image alt:** Decorative icons use `aria-hidden="true"`.
- **Live regions:** `aria-live="polite"` on loading skeletons; `aria-busy` on async content.
- **Focus rings:** `focus-visible:ring-2 focus-visible:ring-brand-600` on interactive elements.
- **Disabled states:** `data-[disabled]:opacity-50`, `pointer-events-none`.
- **Form labels:** All inputs have associated `<Label>` or `aria-label`.
- **Field errors:** `FieldError` component with `aria-invalid` on invalid fields.
- **Color-coded severity:** CPCB AQI badges with semantic colors.
- **Dialog roles:** Radix `Dialog` with `DialogTitle`, `DialogDescription`; `role="menu"`, `role="menuitem"`.

**Weaknesses:**

- **No automated a11y testing:** axe-core / @axe-core/react not integrated.
- **No color contrast audit:** Contrast ratios not programmatically verified.
- **No screen reader testing:** Not tested with NVDA/JAWS/VoiceOver.
- **No keyboard-only end-to-end testing:** Not tested with keyboard only.
- **No `prefers-reduced-motion` handling:** Not checked.

**Evidence:** `frontend/src/components/layout/skip-link.tsx`, `frontend/src/components/dashboard/`, `frontend/vitest.setup.ts`

**Score: 68/100** — Good manual accessibility foundation, but no automated verification.

---

### F. Problem Statement Alignment — 88/100

**Strengths:**

- **Solves the stated problem:** Converts fragmented environmental information into personalized, practical guidance for everyday decisions.
- **Useful air-quality information:** CPCB 2014 AQI with pollutant concentrations, source type, station details, freshness.
- **Observation vs forecast distinction:** Explicit labelling throughout — ground observations vs model forecasts never merged.
- **Pollutant explanations:** CPCB method, dominant pollutant, coverage, basis all disclosed.
- **Personalized recommendations:** Household profile (age bands, health flags), activity windows, member sensitivity all feed into recommendations.
- **Real-world decisions:** SmartRoutine tells users WHEN to do activities; IndoorShield tells users WHAT to do indoors; EcoRoute tells users HOW to travel.
- **Activity planning:** Deterministic scheduler with versioned plans, overrides, and replanning.
- **Indoor air quality:** IndoorShield with sensor registration, readings, assessments, and prioritized actions.
- **Transportation comparison:** EcoRoute with sourced emission factors, mode comparison, null (not invented) for unsupported modes.
- **Transparent impact:** Impact ledger with factor provenance, modelled baseline disclosure ("not a measured baseline"), methodology page.

**Weaknesses:**

- **Impact frontend is local-only:** Backend has full `/impact` endpoints but frontend impact page is deliberately local-only — disconnect between backend capability and frontend exposure.
- **No alerting/push notifications:** Users must actively check; no proactive warnings for pollution peaks.
- **Single household per anonymous session:** Limits multi-household or family sharing scenarios.
- **No street-level hyperlocal forecasting:** Relies on provider data; no micro-location precision.
- **No owned sensor network:** Dependent on third-party providers (Open-Meteo, OpenAQ).

**Unnecessary or insufficiently connected features:** None identified — all 7 modules map directly to the core problem.

**Evidence:** All 7 frontend page routes, all backend service modules, `docs/API_CONTRACT_AUDIT.md`

**Score: 88/100** — Excellent alignment with the problem statement; every module serves a real user need.

---

## C. Innovation Review

| Proposed Differator | Genuinely Implemented? | Technically Different? | Practical Value | Evidence |
|---------------------|----------------------|----------------------|-----------------|----------|
| Pollution-to-Action Intelligence | ✅ Yes | Deterministic rules engine (not LLM-driven) | Tells users WHEN to act, not just what AQI is | `app/domain/routine.py`, `app/services/routine_service.py` |
| SmartRoutine AI | ✅ Yes | Pure-function scheduler with dose estimation, versioned plans | Activity timing based on forecast concentrations | `app/domain/routine.py`, `ENGINE_VERSION="routine-2.0.0"` |
| IndoorShield AI | ✅ Yes | Transparent priority scoring (WHO/ASHRAE/EPA-based) | Prioritized indoor actions with audit trail | `app/domain/indoor_shield.py`, `PRIORITY_HIGH=300` |
| EcoRoute AI | ✅ Yes | Sourced emission factors; null for unsupported modes | Transport comparison without invented numbers | `app/domain/carbon.py`, `app/services/ecoroute_service.py` |
| Grounded SAANS AI Copilot | ✅ Yes | FactPack + fail-closed validation + deterministic fallback | Model can never invent environmental data | `app/services/copilot_service.py`, `app/integrations/ai/validation.py` |

**Assessment:** All five differentiators are genuinely implemented, not planned. The project does not claim industry-first status without evidence. The differentiation is credible: actionability + trustworthiness, not data breadth.

**Improvement recommendation:** Add a "confidence" indicator to each recommendation showing data freshness and source reliability, so users can gauge how much to trust each action.

---

## D. AI Quality Review

| Aspect | Assessment | Evidence |
|--------|-----------|----------|
| Context retrieval | FactPack built server-side from deterministic services; model receives only structured facts | `copilot_service.py::_build_fact_pack` |
| Tool execution | Backend-owned; `tool_executor.py` maps tool names to real service calls with authorization | `app/integrations/ai/tool_executor.py` |
| Structured outputs | Constrained JSON schema (answer, actions, avoid); `extra="forbid"` | `app/integrations/ai/validation.py::AiDraft` |
| Grounding | Fact reference validation; number grounding within 1% tolerance; unsafe content stripping | `parse_and_validate()`, `_numbers_grounded()`, `_strip_unsafe()` |
| Data provenance | All facts carry source, version, retrieval date; citations rebuilt server-side | `app/domain/facts.py::Fact` |
| Prompt injection resistance | Model receives no user text in system instruction; system instruction fixed; user message in contents only | `gemini.py::generate()` |
| Error handling | Fail-closed: rejected/invalid/over-budget → deterministic fallback | `copilot_service.py::_explain()` |
| Fallback behavior | Deterministic composer generates actionable advice without model | `app/integrations/ai/fallback.py::compose_fallback()` |
| Token efficiency | Model only for explanations; deterministic services handle all compute | Architecture decision |
| Response quality | Max 600 chars answer; max 5 actions; max 3 avoid items; 3 sentences (routine) | Schema constraints |

**Assessment:** The AI integration is thoughtfully designed with appropriate constraints. The model is correctly positioned as an explainer, not a decision-maker. The fail-closed validation is a strong security feature.

**Improvement recommendation:** Add latency tracking and budget exhaustion metrics to the UI so users understand when they're seeing deterministic vs AI-generated content (already partially done via `explanation.status` field).

---

## E. User Experience Review

### First-Time User Journey

**Current state:**

1. **Landing page:** Marketing site with hero, capability strips, problem/solution sections, CTA to dashboard. Clear value proposition.
2. **Dashboard:** Location gate — user must select a location before seeing data. Honest empty states ("No readings are generated locally").
3. **Air quality:** Detailed CPCB AQI, pollutant grid, provenance panel, forecast/history tabs (render only from provider responses).
4. **Family intelligence:** Session start → household profile → activity preferences → recommendations.
5. **SmartRoutine:** Household → members → activities → generate plan → versioned schedule with overrides.
6. **IndoorShield:** Assessment → sensor registration → readings → prioritized actions.
7. **EcoRoute:** Origin/destination → mode comparison → emission estimates.
8. **Copilot:** Grounded chat with citations; graceful unavailability states.

**Strengths:**

- Every unavailable state is honest (no fake data, no sample curves)
- Location-first onboarding prevents showing meaningless data
- Clear disclaimers ("General guidance, not medical advice")
- Provenance transparency (provider, source type, freshness)
- Skip link and keyboard navigation

**Weaknesses:**

- **No guided onboarding:** First-time user must discover features independently
- **No alerting:** Users must actively check for pollution peaks
- **Impact page disconnected:** Frontend impact is local-only despite full backend API
- **Mobile layout:** Not evaluated (no mobile testing performed)
- **Empty states:** Generally good, but some could be more actionable

**Recommended first-time journey:**

1. Landing → select location (mandatory gate)
2. Dashboard → see current AQI + provenance
3. Air quality → understand pollutants + forecast
4. Family → create household profile + activity windows
5. SmartRoutine → generate daily plan
6. Copilot → ask questions with citations
7. IndoorShield → assess home + register sensors
8. EcoRoute → compare transport options

---

## F. Performance and Reliability

**Measured:**

| Metric | Value | Source |
|--------|-------|--------|
| Backend tests | 264 passed, 0 failed | `pytest --cov` |
| Backend duration | ~6 minutes (full DB suite) | Test run |
| Frontend tests | All passing | `vitest run` |
| Frontend build | 12 routes, clean | `next build` |
| Backend coverage | 77.53% lines | `coverage.xml` |
| Frontend coverage | 74.1% branches | `lcov.info` |
| Tracked repo size | 1.74 MB | `git ls-files` |

**Not measured (no deploy access):**

- Frontend load performance (LCP, FID, CLS)
- Backend response time
- API failure rates
- Database query performance
- External provider latency
- Gemini latency
- Bundle size

**Reliability features:**

- Circuit breakers per provider
- TTLCache for responses
- AI daily budget with fallback
- Deterministic fallback for all AI features
- Graceful degradation when providers unavailable
- No invented measurements on failure

---

## G. Improvement Backlog

| Priority | Problem | Evidence | Expected Improvement | Affected Files | Complexity | Regression Risk | Validation |
|----------|---------|----------|---------------------|----------------|------------|-----------------|------------|
| P0 | Backend coverage below 80% CI gate | 77.53% vs 80% `fail_under` | CI passes; more confidence in critical paths | `gemini.py`, `tool_executor.py`, `impact_service.py`, `indoor_shield_service.py`, `routine_service.py` | Medium | Low | `pytest --cov` |
| P0 | Fix character encoding issues (replacement chars) | � characters in source files | Clean source, no encoding bugs | Multiple `.py` files | Low | Low | `mypy`, `ruff` |
| P1 | Add frontend a11y automated testing | No axe-core integration | Catch regressions; verify contrast | `vitest.setup.ts`, new test files | Medium | Low | `npm run test:coverage` |
| P1 | Add E2E tests for critical user journeys | No E2E tests | Catch integration bugs | New `tests/e2e/` directory | High | Low | Playwright/Cypress |
| P1 | Add load/performance tests | Not measured | Establish baseline; detect regressions | New test files | Medium | Low | k6/artillery |
| P1 | Add deployment config (`render.yaml`/`vercel.json`) | No deploy files | Enable production deployment | New config files | Low | None | Deploy verification |
| P2 | Add confidence indicator to recommendations | No data reliability signal | Users can gauge trust in recommendations | Frontend components | Medium | Low | Unit tests |
| P2 | Add alerting/push notifications | No proactive warnings | Users informed of pollution peaks | Backend + frontend | High | Medium | Integration tests |
| P2 | Connect impact frontend to backend | Local-only frontend impact | Full feature exposure | `frontend/src/components/impact/` | Medium | Medium | API tests |
| P3 | Add bundle size analysis | Not configured | Monitor bundle growth | `next.config.ts` | Low | None | Build output |
| P3 | Add Core Web Vitals measurement | Not measured | Performance baseline | New monitoring | Low | None | Lighthouse |
| P3 | Fix encoding in markdown/docs | Various | Clean documentation | `docs/` | Low | None | Review |

---

## H. Judge Simulation

### Judge 1: Software Engineering

**Strongest aspect:** Clean separation of domain logic from services and API; deterministic engines with versioning; fail-closed AI validation.

**Weakest aspect:** Critical service files under-tested (gemini.py 36%, tool_executor.py 39%, impact_service.py 36%).

**Most important technical concern:** Backend coverage below CI gate means the project would fail its own quality gate in CI.

**Questions they would ask:**
- Why is `impact_service.py` (the sustainability ledger) only 36% covered?
- How do you handle database migrations in production without downtime?
- What's your strategy for the `gemini.py` file that's 36% covered?

**Evidence they expect to see:** Coverage reports, migration scripts, CI pipeline output, test execution logs.

**Recommendations:** Add tests for the 5 under-covered service files before submission; fix encoding issues.

---

### Judge 2: AI Architecture

**Strongest aspect:** FactPack + fail-closed validation; model correctly positioned as explainer not decision-maker; structured outputs with fact reference validation.

**Weakest aspect:** No token efficiency metrics; no latency tracking for model calls; budget exhaustion not surfaced to users.

**Most important technical concern:** The model could still produce plausible-sounding but subtly wrong advice if numbers happen to match FactPack values but are used in wrong contexts.

**Questions they would ask:**
- How do you prevent the model from giving medical advice disguised as air-quality advice?
- What happens when Gemini is rate-limited during peak usage?
- How do you measure explanation quality?

**Evidence they expect to see:** Validation logic, fallback responses, latency logs, budget metrics.

**Recommendations:** Add medical term detection beyond the current regex; add latency tracking; surface deterministic vs AI-generated status to users (partially done).

---

### Judge 3: Environmental Technology

**Strongest aspect:** CPCB 2014 method explicitly used; observation vs forecast distinction; sourced emission factors with provenance; modelled baseline clearly labelled as assumption.

**Weakest aspect:** No hyperlocal forecasting; no owned sensor network; no historical trend analytics.

**Most important technical concern:** Reliance on third-party providers (Open-Meteo, OpenAQ) means data quality and availability are outside the team's control.

**Questions they would ask:**
- How do you validate provider accuracy against reference monitors?
- What happens when all providers are unavailable?
- How is the modelled car baseline (16 km/day) justified?

**Evidence they expect to see:** Factor source URLs, provider health monitoring, baseline methodology documentation.

**Recommendations:** Add provider health dashboard; document baseline assumptions more prominently; add historical data retention.

---

### Judge 4: Product and UX

**Strongest aspect:** Honest empty states; location-first onboarding; clear disclaimers; provenance transparency.

**Weakest aspect:** No guided onboarding; no alerting; impact page disconnected from backend.

**Most important technical concern:** Users may not understand the difference between observed and forecast data despite labelling.

**Questions they would ask:**
- How does a first-time user know what to do first?
- What happens when pollution peaks at 2 AM?
- Why is the impact page local-only?

**Evidence they expect to see:** User journey mockups, onboarding flows, alerting design, impact page screenshots.

**Recommendations:** Add guided onboarding; add push/email alerts for peaks; connect impact frontend to backend API.

---

### Judge 5: Security and Reliability

**Strongest aspect:** Bearer tokens with SHA-256 hashes; health-data consent gating; CORS restrictions; security headers; no secrets in repo.

**Weakest aspect:** No penetration testing; production CORS origins unverified; no OAuth/MFA.

**Most important technical concern:** Anonymous session model means no account recovery — clearing browser storage loses all data.

**Questions they would ask:**
- How do you handle session hijacking?
- What's your data retention policy?
- How do you test for injection attacks?

**Evidence they expect to see:** Penetration test reports, security scan outputs, data retention policy, incident response plan.

**Recommendations:** Commission penetration testing; document data retention; add session security features.

---

## I. Final Presentation Recommendations

### 10 Questions & Answers (matching actual implementation)

| Question | Answer |
|----------|--------|
| **What problem does the project solve?** | Urban residents get fragmented air-quality information but lack personalized, practical guidance. SAANS SAATHI AI converts environmental data into actionable recommendations for timing activities, indoor protection, and sustainable transport. |
| **Why is an ordinary AQI dashboard insufficient?** | An AQI number doesn't tell you when to walk, what to do indoors, or how to travel. SAANS SAATHI AI converts AQI into specific actions: SmartRoutine schedules activities around forecast pollution, IndoorShield prioritizes home improvements, EcoRoute compares transport emissions. |
| **What makes SAANS SAATHI AI different?** | Three things: (1) Pollution-to-action via deterministic rules, not just data display. (2) Trustworthiness — fail-closed AI validation, sourced emission factors, observation/forecast distinction, no invented data. (3) Privacy — anonymous sessions, no PII to model, health-data consent gating. |
| **How does SmartRoutine work?** | It's a deterministic scheduler (`routine-2.0.0`) that takes household activities, member profiles, and 48-hour forecast concentrations. It enumerates candidate start times, estimates inhaled dose using the exposure model, and selects the lowest-score non-overlapping schedule. Versioned plans with overrides and replanning. |
| **How is Gemini integrated?** | Gemini only rephrases pre-computed plans — it never makes scheduling or emission decisions. It receives a FactPack (server-built deterministic facts only) and must return validated JSON. All output is fail-closed: rejected/invalid/over-budget responses fall back to deterministic answers. |
| **How do you prevent fabricated environmental readings?** | Multiple layers: (1) FactPack contains only server-produced values. (2) Fact reference validation — all cited IDs must exist. (3) Number grounding — all numeric claims must match FactPack values. (4) Unsafe content stripping. (5) Deterministic fallback when model is unavailable. |
| **How are emissions calculated?** | Using sourced emission factors (DEFRA 2023 for bus/train, IPCC 2006 for walking, CEA v22 for grid) with haversine distance estimates. Modes without verified factors return null — never invented numbers. Each result carries factor key, value, version, and source URL. |
| **What happens when external providers fail?** | Circuit breakers per provider; TTLCache serves stale data when available; graceful degradation to labelled stale data; 503 when all sources exhausted. Never invents measurements. |
| **How is user information protected?** | Bearer tokens with SHA-256 server-side digests; no names/emails/phones stored; health flags require explicit consent (403 otherwise); FactPack excludes PII from model; session-scoped rate limiting; security headers (nosniff, DENY framing, no-referrer). |
| **What is the next development milestone?** | Clear backend coverage CI gate (add tests for under-covered services), add deployment configuration, connect impact frontend to backend API, add automated accessibility testing, verify production deployment. |

### Presentation Strengths to Emphasize

1. **Every differentiator is implemented, not planned** — demo the actual working features
2. **Fail-closed AI** — show what happens when the model is unavailable (deterministic fallback)
3. **Provenance transparency** — show the provenance panel with provider, source type, freshness
4. **No invented data** — demonstrate null values for unsupported transport modes
5. **Privacy by design** — explain anonymous session model and consent gating

### Presentation Weaknesses to Address

1. **Don't claim industry-first** — position as "credible niche player" not "first mover"
2. **Be honest about limitations** — impact page local-only, no mobile app, no alerting
3. **Don't overstate accuracy** — emphasize labelled assumptions and modelled data

---

## J. Final Verdict

**Internal score: 70.1/100**

SAANS SAATHI AI is a **solid, well-engineered project** with genuine differentiators in actionability and trustworthiness. It is not competition-leading, but it is credible and functional.

**Key risks:**
1. Backend coverage below CI gate (could fail automated quality checks)
2. Critical service files under-tested (gemini.py, tool_executor.py, impact_service.py)
3. No production deployment verification
4. No automated accessibility testing
5. No penetration testing

**Recommendation:** The project is suitable for submission with documented limitations. Address the P0 items (coverage gate, encoding issues) before submission to maximize competitive position.

**This is an internal assessment. It does not guarantee leaderboard rank or official hackathon results.**
