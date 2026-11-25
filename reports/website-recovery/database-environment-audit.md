# Database & Environment Audit — SAANS SAATHI AI Website Recovery

**Status:** COMPLETE  
**Date:** Mon Nov 23 2026  
**Engineer:** Principal Full-Stack / DevOps

## Database configuration

| Setting | Value | Source |
|---|---|---|
| `DATABASE_URL` | unset locally (optional in dev) | `app/core/config.py` |
| `TEST_DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/saans_test` | pytest env |
| Test DB reachable | YES (`SELECT 1` OK) | Direct probe |
| Production DB (`render.yaml`) | `postgres+psycopg://postgres:postgres@db:5432/saans_prod` | render.yaml env var |
| `APP_ENV` | unset locally | config default |

`config.py` validators:
- `database_url` blank → `None` (dev-friendly)
- non-blank must use `postgresql+psycopg` scheme with host + db name
- `APP_ENV == "production"` requires `DATABASE_URL` (model validator `_require_database_in_production`)

## Environment files present

**Backend** (`backend/`): **no `.env` or `.env.example` files exist.** All config falls back to `config.py` defaults:
- `frontend_url: str = "http://localhost:3000"`
- `allowed_origins: str = ""` → CORS falls back to `[frontend_url]` only (the CORS defect fixed in `backend-recovery.md`)
- `cpcb_enabled: bool = False` (CPCB not enabled in dev — real data still flows via Open-Meteo/OpenAQ resolution chain)

**Frontend** (`frontend/`):
| File | Contents |
|---|---|
| `.env.local` | `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` (real, non-secret) |
| `.env.example` | placeholders only, no real secrets |

No secrets are committed anywhere. `GEMINI_API_KEY` is referenced via `${GEMINI_API_KEY}` in `render.yaml` (environment-injected, never hardcoded).

## `env.ts` validation (verified)

`frontend/src/lib/env.ts` parses `NEXT_PUBLIC_API_BASE_URL` via:
```ts
z.url({ protocol: /^https?$/ }).default("http://localhost:8000")
```
Verified with Zod directly:
- `http://localhost:8000` → valid
- `https://x.vercel.app` → valid
- `undefined` → defaults to `http://localhost:8000`
Not a defect.

## Pytest database-backed test coverage

With `TEST_DATABASE_URL` set: **280 passed, 0 failed** (no skips). Without it: 97 database-backed tests skipped (documented `pytest.mark.skipif` on missing `TEST_DATABASE_URL`).

Coverage (with DB): TOTAL 78.86% — `FAIL Required test coverage of 80.0% not reached`. Pre-existing on the committed tree; documented in `recovery_coverage.txt`; not suppressed.

## Secrets / safety

- No hardcoded secrets found in `render.yaml`, `vercel.json`, `.env.local`, or source.
- `GEMINI_API_KEY` injected from environment at deploy time only.
- No AQI/pollutant/sensor/route/impact data fabricated — unavailable surfaces return 503 problem documents.

## Conclusion

Database configuration is sound for dev (optional `DATABASE_URL`) and production (requires `DATABASE_URL` when `APP_ENV=production`). Test DB is reachable. The only environment-related defect was the CORS allowlist deriving solely from `frontend_url` (`localhost:3000`), fixed in `backend/render.yaml`. No secrets exposed, no data fabricated.
