# SAANS SAATHI AI — Performance Audit

**Audit date:** 2026-11-21  
**Scope:** Build size, route count, query patterns, caching, AI budget, frontend bundle

---

## Build & Bundle

| Metric | Value | Status |
|--------|-------|--------|
| Frontend build routes | 12 routes | ✓ |
| Frontend build | `npm run build` — clean, no errors | ✓ |
| Ignored working tree | `node_modules` 563 MB, `.next` 283 MB, `.venv` 151 MB | Not tracked |
| Tracked repo size | ~3 MB (target under 10 MB per CI) | ✓ |

## Frontend Performance

| Area | Implementation | Status |
|------|---------------|--------|
| Code splitting | Next.js App Router with route-based splitting | ✓ |
| Dynamic imports | `map-canvas.tsx` loaded with `next/dynamic` (SSR off, skeleton loading) | ✓ |
| Image optimization | Next.js Image component with `next/font` (Inter, self-hosted) | ✓ |
| Caching | `useSyncExternalStore` with snapshot cache for localStorage; stable references prevent re-renders | ✓ |
| Charts | Recharts (jsdom stubbed in tests) — renders only from provider responses, no sample curves | ✓ |
| Unavailable states | `DataState` component shows loading/unavailable rather than skeleton indefinitely | ✓ |

## Backend Performance

| Area | Implementation | Status |
|------|---------------|--------|
| Provider caching | TTLCache for air-quality provider responses; avoids repeated network calls | ✓ |
| Circuit breaker | Air-quality provider circuit opens on repeated failures; falls back gracefully | ✓ |
| AI budget | Daily request budget; exhausted → deterministic fallback without model call | ✓ |
| Deterministic scheduling | SmartRoutine engine is pure computation — no LLM for scheduling | ✓ |
| Async DB | SQLAlchemy async with NullPool for tests; connection pooling for production | ✓ |
| Query pagination | Impact activities, routine history, family recommendations all paginated | ✓ |

## AI / LLM Performance

| Area | Implementation | Status |
|------|---------------|--------|
| Model usage | Gemini only for explanations (not scheduling); deterministic fallback on failure/budget exhaustion | ✓ |
| Output validation | All model output validated against FactPack; rejected output falls back to deterministic text | ✓ |
| FactPack size | Bounded facts (≤5 blocks + counts + coverage); no raw coordinates or names | ✓ |
| Prompt length | System instruction + FactPack JSON < 500 characters response | ✓ |

## Database Performance

| Area | Implementation | Status |
|------|---------------|--------|
| Indexes | Not explicitly reviewed; ORM-generated indexes on FKs and primary keys | Partial |
| Connection pooling | NullPool for tests; production pool configuration needed | Partial |
| Query efficiency | Repository methods use SQLAlchemy `select` with filters; no N+1 detected in reviewed code | Partial |

## Frontend Coverage vs Performance

| Metric | Measured | CI Gate | Target |
|--------|----------|---------|--------|
| Statements | 86.9% | 70% | 80% |
| Branches | 74.1% | 70% | 80% |
| Functions | 87.8% | 70% | 80% |
| Lines | 87.1% | 70% | 80% |

## Gaps / Limitations

| Area | Detail |
|------|--------|
| No production load testing | Cannot test under production traffic without deploy access |
| No Core Web Vitals measurement | Lighthouse/CRuX not run |
| No database query profiling | EXPLAIN ANALYZE not performed |
| No bundle size analysis | `next-bundle-analyzer` not configured |
| Production DB pooling | Connection pool settings not configured for production |
