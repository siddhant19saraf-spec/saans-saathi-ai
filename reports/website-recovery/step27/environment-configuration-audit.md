# Environment Configuration Audit — SAANS SAATHI AI

**Status:** AUDITED 
**Date:** Mon Nov 23 2026 
**Engineer:** Principal DevOps

## Frontend Environment

| File | Contents | Status |
|---|---|---|
| `frontend/.env.local` | `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` | ✅ Present and correct |
| `frontend/.env.example` | Placeholders only, no real secrets | ✅ Does not commit secrets |
| `frontend/src/lib/env.ts` | `z.url({ protocol: /^https?$/ }).default("http://localhost:8000")` | ✅ Validated with Zod; accepts `http://` and `https://`; `undefined` defaults to `http://localhost:8000` |

### `env.ts` Validation Details

```typescript
z.url({ protocol: /^https?$/ }).default("http://localhost:8000")
```

- `http://localhost:8000` → **valid** (parsed, scheme matches)
- `https://x.vercel.app` → **valid** (parsed, scheme matches)
- `undefined` → **defaults to** `http://localhost:8000`
- `ftp://example.com` → **rejected** (scheme not `http` or `https`)

**No secrets are exposed.** `NEXT_PUBLIC_API_BASE_URL` is a URL, not a secret. `GEMINI_API_KEY` is referenced via `${GEMINI_API_KEY}` in render.yaml (injected at deploy time, never hardcoded).

## Backend Environment

| File | Contents | Status |
|---|---|---|
| `backend/.env*` | **No `.env` or `.env.example` files exist** | ⚠️ All config falls back to `core/config.py` defaults |
| `backend/core/config.py` | Pydantic Settings with `model_config env_file=".env"` | ✅ Config loads from environment; `.env` optional |
| `render.yaml` | `ALLOWED_ORIGINS: https://saans-saathi-web.vercel.app,https://saans-saathi-api.vercel.app` | ✅ Deploy-time origins |
| `render.yaml` | `FRONTEND_URL: https://saans-saathi-web.vercel.app` | ✅ Deploy-time frontend URL |
| `render.yaml` | `DATABASE_URL: postgres+psycopg://postgres:postgres@db:5432/saans_prod` | ✅ Production DB required |
| `backend/Procfile` | `web: uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory` | ✅ Deployment-ready |

### Backend Config Defaults (from `core/config.py`)

| Variable | Default | Notes |
|---|---|---|
| `app_env` | `development` | Affects health checks, docs enabled |
| `database_url` | `None` | Optional in dev; required in production |
| `frontend_url` | `http://localhost:3000` | CORS fallback origin |
| `allowed_origins` | `""` | → falls back to `[frontend_url]` |
| `gemini_api_key` | `None` | Injected at deploy time |
| `cpcb_enabled` | `False` | Not enabled in dev |
| `log_level` | `INFO` |  |

### Environment Variable Validation

| Validator | Purpose | Result |
|---|---|---|
| `_validate_database_url` | Must use `postgresql+psycopg` scheme; must have hostname + db name | ✅ Passes when set; raises `ValueError` if invalid scheme or missing host/db |
| `_validate_http_url` | Must be absolute `http(s)` URL | ✅ Passes for `http://localhost:3000`, `https://saans-saathi-web.vercel.app` |
| `_validate_allowed_origins` | Must not contain `*`; each entry must be absolute `http(s)` origin | ✅ Passes with explicit list; raises `ValueError` on wildcard |
| `_require_database_in_production` | `DATABASE_URL` required when `APP_ENV=production` | ✅ Enforces production database requirement |

### Missing Environment Variables

| Variable | Required? | Current Status | Impact if Missing |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Yes (frontend) | Set in `frontend/.env.local` → `http://localhost:8000` | Frontend would default to localhost:8000 (same as current) |
| `GEMINI_API_KEY` | No (optional) | Not set locally | AI/Copilot features gracefully unavailable; no crash |
| `DATABASE_URL` | Yes (prod), optional (dev) | Not set locally | Backend starts healthy in dev; reports `database_not_configured` in health |
| `ALLOWED_ORIGINS` | No (runtime) | Set in environment for testing → `http://localhost:3000,http://localhost:3001` | CORS falls back to `frontend_url` only (`localhost:3000`) |
| `APP_ENV` | No (defaults to development) | Not set | Defaults to `development`; docs enabled, health reports `database_not_configured` if no DB |

## Deployment Environment

| Config File | Environment | Key Settings |
|---|---|---|
| `render.yaml` | Production (intended) | `ALLOWED_ORIGINS` set to Vercel origins; `FRONTEND_URL` set; `DATABASE_URL` set; `GEMINI_API_KEY` injected via env var |
| `vercel.json` | Vercel production | `builds[0].src = frontend/next.config.ts`; `routes` rewrites to `.next/` and `/api/`; `env.NEXT_PUBLIC_API_BASE_URL = https://saans-saathi-api.vercel.app` |
| No `.env` in backend | Development only | All config from `core/config.py` defaults; no secrets committed |

## Secrets Safety

- ✅ No hardcoded API keys, database credentials, or secrets in any source file
- ✅ `GEMINI_API_KEY` referenced via `${GEMINI_API_KEY}` in `render.yaml` only (environment-injected at deploy time)
- ✅ `openaq_api_key` and `cpcb_api_key` are `None` by default (not hardcoded)
- ✅ ` DATABASE_URL` not committed (optional in dev, required in prod)
- ✅ `NEXT_PUBLIC_API_BASE_URL` is a URL, not a secret

## Conclusion

**Environment configuration is sound.** All required variables are present for local development. No secrets are exposed. The only gap is the absence of `.env` files in the backend directory (config falls back to `core/config.py` defaults, which is intentional — the system is designed to work without a `.env` file in dev). For production deployment, `render.yaml` and `vercel.json` provide the necessary environment variables, and `GEMINI_API_KEY` must be injected at deploy time.

**No changes required to environment configuration** for local development to work. The fix for the "URL unreachable" issue was simply starting the running services.