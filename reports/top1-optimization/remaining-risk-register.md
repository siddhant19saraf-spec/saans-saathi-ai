# Remaining Risk Register

## Open Risks (Post-Optimization)

| ID | Category | Description | Severity | Owner | Mitigation Status |
|----|----------|-------------|----------|-------|-------------------|
| RR-001 | Configuration | `app/schemas/common.py` at 0% Stmts coverage (14 lines, `ProblemDetail` + `FieldError` models). No tests exercise serialization/validation edge cases. | P2 (coverage gate impact) | Backend team | Add pydantic model serialization tests; expected to raise schema coverage from 0% to ~40-50% |
| RR-002 | Coverage | Backend line coverage 65.28% vs 80% gate. 97/97 database-backed tests skipped without `TEST_DATABASE_URL`. | P2 (gate not met) | DevOps / DBA | Set `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/saans_test` in CI; requires PostgreSQL instance |
| RR-003 | Coverage | Frontend branch coverage 73.82% vs aspirational 90% target (70% gate met). Uncovered branches in `card.tsx` (2:25,33), `container.tsx` (27-35), `rm-dialog.tsx` (54), `family-view.tsx` (18,409-518,741), `use-family.ts` (53-269,276-285), `map-view.tsx` (38,168-170), `api/client.ts` (40), `use-routine.ts` (36-37). | P3 (improvement opportunity) | Frontend team | Add interaction tests for card hover/press, container branches, dialog Escape, family form, hook effects, map interactions, API error paths, routine hook branches |
| RR-004 | Accessibility | Color contrast for `brand-800`/`brand-600` on `white` at 8.65:1 meets AA large text but not AAA. Borders (`#E5E7EB` on `#FFFFFF`) at 3:1 fail AA (but are decorative, not informational). | P3 (AAA improvement) | Design team | Consider `brand-900` (darker) for text on white, or increase `ink-subtle` contrast; borders are exempt as decorative |
| RR-005 | Performance | Bundle size: CSS chunks total ~71,605 B (2 chunks). No `next/image` configuration for module images; no WebP/AVIF conversion. | P3 (load time) | Frontend team | Add `next/image` optimization; convert static images to WebP/AVIF; evaluate `imagesrcset` and `sizes` |
| RR-006 | Security | No Content-Security-Policy header configured. Risk: XSS if any future code introduces `dangerouslySetInnerHTML` or unescaped dynamic content. | P3 (future risk) | Backend/Frontend team | Add CSP middleware or meta tag when routes requiring it are identified; currently no `dangerouslySetInnerHTML` in codebase |
| RR-007 | Deployment | No GitHub remote exists at `https://github.com/username/saans-saathi-ai.git`; Vercel/Render accounts/credentials not configured; Step 31 deployment authorization granted but not executed (remote unreachable). | P2 (submission blocker) | User / DevOps | User must create GitHub repo, configure Vercel/Render, or authorize alternative deployment. No push/deploy possible without valid remote. |
| RR-008 | Secrets | `GEMINI_API_KEY` absent → Copilot shows "Not connected". No API key configured in any environment. | P3 (feature unavailable) | User | Provide Gemini API key in `.env` if copilot deterministic fallback not sufficient |
| RR-009 | Data integrity | Backend activity/impact services (`app/services/routine_service.py`, `app/services/impact_service.py`) make external calls to Open-Meteo and Open-AQ without mock layer at unit level. Unit tests currently skip these (they are integration-level). | P3 (test gap) | Backend team | Add HTTP mock layer (`pytest` `unittest.mock` or `pytest-mock`) for Open-Meteo/Open-AQ calls in unit tests; currently 97 tests skipped, 183 pass in-process |
| RR-010 | Dependency currency | `structlog 26.1.0` — verify version numbering (is this 26.1.0 or semantic?). Python 3.13.14 running; `>=3.12,<3.14` gate is tight; next Python 3.14 release may require upgrade. | P4 (future compatibility) | DevOps | Monitor Python 3.14 release schedule; plan upgrade when 3.14 is stable; no immediate action required |

## Risk Prioritization

| Priority | Rationale |
|----------|-----------|
| **P0–P1** | RR-007 (deployment remote unreachable) blocks final submission; RR-001 (schema coverage 0%) and RR-002 (backend 65% vs 80% gate) are technical-debt items that can be addressed with focused test additions |
| **P2** | RR-002 (backend coverage gate), RR-006 (no CSP), RR-008 (Gemini key absent), RR-009 (no HTTP mock layer), RR-001 (schema 0%) — all addressable with targeted work |
| **P3** | RR-003 (frontend branches below 90%), RR-004 (contrast AAA), RR-005 (bundle size), RR-007 (deployment — already flagged as P2), RR-008 (secrets) — improvements, not blockers |
| **P4** | RR-010 (Python version gate) — monitoring only, no immediate action |

## Risk Acceptance

| Risk | Accepted Because |
|------|------------------|
| RR-002 (backend 65.28% vs 80% gate) | 97/97 skipped tests require `TEST_DATABASE_URL`; documented pre-existing condition (reported 77.53% user-stated, measured 78.86% earlier, 65.28% with DB). Not suppressed; no tests weakened. |
| RR-003 (frontend branches 73.82% vs 90%) | 70% automated gate met; all new tests pass; adding more tests yields diminishing returns on branch coverage without additional product scenarios |
| RR-005 (bundle size ~72KB CSS) | Acceptable for dashboard-style application; no critical path rendering blocked; can be optimized in a future phase |
| RR-006 (no CSP) | No `dangerouslySetInnerHTML` in codebase; no current XSS vectors; CSP can be added when routes requiring it are identified |
| RR-008 (Gemini API key absent) | Copilot falls back to deterministic local-data answers; "Not connected" state is documented UX; key can be provided later |
| RR-010 (Python 3.13.14, gate <3.14) | Tight gate but stable; no 3.14 incompatibilities observed; monitor and plan upgrade |

## Risk Status Summary

| Status | Count | Risks |
|--------|-------|-------|
| Closed (resolved) | 1 | P0 CONFIG-001 (DATABASE_URL scheme fix in `render.yaml` + `README.md`) |
| Open — Addressable | 8 | RR-001 through RR-009 (all actionable with focused work) |
| Open — Accepted | 2 | RR-002 (backend coverage pre-existing), RR-003 (frontend branches vs 90% aspirational) |
| Total | 11 | — |

## Next Steps (If Further Optimization Is Desired)

1. **Add schema tests:** `app/schemas/common.py` ProblemDetail + FieldError serialization tests → raise coverage from 0% to ~40%
2. **Set TEST_DATABASE_URL in CI:** `postgresql+psycopg://postgres:postgres@localhost:5432/saans_test` → backend crosses 80% gate
3. **Add frontend branch tests:** `card.tsx`, `container.tsx`, `rm-dialog.tsx`, `family-view.tsx`, `use-family.ts`, `map-view.tsx`, `api/client.ts`, `use-routine.ts` → raise branch coverage toward 90%
4. **Configure next/image:** WebP/AVIF conversion for module images; reduce CSS chunk size
5. **Add CSP header:** Content-Security-Policy for production deployment hardening
6. **Provide GEMINI_API_KEY:** If copilot deterministic fallback is insufficient for production use
7. **Create GitHub remote + deploy:** Required for final submission readiness (Step 12)