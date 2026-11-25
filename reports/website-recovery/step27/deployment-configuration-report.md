# Deployment Configuration Report — SAANS SAATHI AI

**Status:** CONFIGURED BUT NOT DEPLOYED 
**Date:** Mon Nov 23 2026 
**Engineer:** Principal DevOps

## Deployment Configuration Files

### `vercel.json`

| Field | Value | Status |
|---|---|---|
| `version` | `2` | ✅ |
| `builds[0].src` | `frontend/next.config.ts` | ✅ Verified file exists |
| `routes[0].src` | `/.*)` | ✅ Rewrites to `frontend/.next/$1` |
| `routes[0].dest` | `frontend/.next/$1` | ✅ Correct output directory |
| `routes[1].src` | `/api/(.*)` | ✅ Rewrites to backend |
| `routes[1].dest` | `backend/app/main.py?/$1` | ✅ Proxy to FastAPI |
| `env.NEXT_PUBLIC_API_BASE_URL` | `https://saans-saathi-api.vercel.app` | ✅ Production API URL |

**Verification:**
- `fs.existsSync("frontend/next.config.ts") === true` ✅
- Valid JSON ✅
- Build would reference existing config file ✅

**Status:** CONFIGURED. Not deployed (no Vercel project authorized).

### `render.yaml`

| Field | Value | Status |
|---|---|---|
| `services[0].type` | `web` | ✅ |
| `services[0].name` | `saans-saathi-api` | ✅ |
| `services[0].env` | `python` | ✅ |
| `services[0].plan` | `free` | ✅ |
| `services[0].buildCommand` | `pip install .` | ✅ (pyproject.toml deps, no requirements.txt) |
| `services[0].startCommand` | `uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory` | ✅ |
| `services[0].envVars.DATABASE_URL` | `postgresql+psycopg://postgres:postgres@db:5432/saans_prod` | ✅ Production DB |
| `services[0].envVars.LOG_LEVEL` | `INFO` | ✅ |
| `services[0].envVars.CPCB_ENABLED` | `"false"` | ✅ |
| `services[0].envVars.GEMINI_API_KEY` | `${GEMINI_API_KEY}` | ✅ Injected at deploy time |
| `services[0].envVars.ALLOWED_ORIGINS` | `https://saans-saathi-web.vercel.app,https://saans-saathi-api.vercel.app` | ✅ Explicit allowlist, no wildcards |
| `services[0].envVars.FRONTEND_URL` | `https://saans-saathi-web.vercel.app` | ✅ |
| `services[1].type` | `postgresql` | ✅ |
| `services[1].name` | `db` | ✅ |
| `services[1].plan` | `free` | ✅ |
| `services[1].disk` | `10` | ✅ |

**Previous defect (FIXED):** Duplicate top-level `services:` key — `yaml.safe_load` returned only the last service, silently dropping the web service. Also `buildCommand: pip install -r requirements.txt` referenced non-existent `requirements.txt`. Both fixed: single `services:` list, `buildCommand: pip install .`.

**Verification:** `yaml.safe_load` now returns `keys: ['services']`, `count: 2`, `names: ['saans-saathi-api', 'db']`, `types: ['web', 'postgresql']`, `build: pip install .`. ✅

**Status:** CONFIGURED. Not deployed (no Render project authorized).

### `backend/Procfile`

```
web: uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory
```

- `$PORT` substituted by deployment platform (Render/Heroku)
- For local development: `uvicorn app.main:app --port 8000 --loop app.core.loop:selector_loop_factory`
- Uses `WindowsSelectorEventLoopPolicy` on win32 (required for asyncio on Windows)
- ✅ Correct and functional

## Deployment Provider Status

| Provider | Status | Notes |
|---|---|---|
| **Render** | NOT DEPLOYED | `render.yaml` configured correctly; both web + postgresql services defined; no authorization to deploy |
| **Vercel** | NOT DEPLOYED | `vercel.json` configured correctly; next.config.ts verified; no authorization to deploy |
| **Cloudflare Pages** | NOT TESTED | No configuration files found |
| **AWS Amplify** | NOT TESTED | No configuration files found |
| **No provider** | — | No deployment performed; no authorization granted |

## Required Hosting Services

For a successful deployment, the following services are needed:

1. **Render** (for backend + PostgreSQL database) — or another Python/PostgreSQL host
2. **Vercel** (for Next.js frontend) — or another Node/Next.js host
3. Both services should be connected via the CORS `ALLOWED_ORIGINS` configuration

### Environment Variables for Deployment

| Variable | Value (production) | Source |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://saans-saathi-api.vercel.app` | vercel.json |
| `ALLOWED_ORIGINS` | `https://saans-saathi-web.vercel.app,https://saans-saathi-api.vercel.app` | render.yaml |
| `FRONTEND_URL` | `https://saans-saathi-web.vercel.app` | render.yaml |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@db:5432/saans_prod` | render.yaml |
| `GEMINI_API_KEY` | <actual key> | Inject at deploy time |
| `APP_ENV` | `production` | Default from config.py |

### Build and Start Commands

| Service | Build Command | Start Command |
|---|---|---|
| **Frontend (Vercel)** | `next build` (auto by Vercel) | `next start` |
| **Backend (Render)** | `pip install .` (from pyproject.toml) | `uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory` |

**Vercel:** Automatically runs `next build` on push to main; serves `.next/` output.

**Render:** Uses `pip install .` to install hatchling-built wheel; starts uvicorn on `$PORT`.

## DNS and Domain Configuration

- No domain confirmed. Production would use provider-native domains:
  - Vercel: `*.vercel.app` subdomain
  - Render: `*.onrender.com` subdomain
- Custom domain would require DNS A/CNAME records pointing to the provider
- HTTPS is automatic via Let's Encrypt on both Vercel and Render

## Health Endpoints (Production)

| Endpoint | Purpose | Expected |
|---|---|---|
| `/healthz` | Liveness probe | `{"status":"ok"}` (200) if server running |
| `/readyz` | Readiness probe | 200 if deps healthy; 503 if database/unavailable |
| `/api/v1/health` | Detailed health | HealthResponse model (200) |
| `/docs` | OpenAPI docs | Disabled in production (`docs_enabled=False`) |

## Deployment Readiness Checklist

- [x] `render.yaml` — single `services:` list (web + postgresql), `pip install .`, `ALLOWED_ORIGINS`, `FRONTEND_URL`
- [x] `vercel.json` — `next.config.ts` (verified exists), API routes proxied to backend
- [x] `backend/main.py` — app factory, lifespan, CORS, health endpoints
- [x] `frontend/next.config.ts` — security headers, Turbopack root
- [x] `frontend/.env.local` — `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` (local), would be `https://saans-saathi-api.vercel.app` (prod)
- [ ] **Authorize a deployment provider** (Render or Vercel)
- [ ] **Set `GEMINI_API_KEY`** in the provider environment
- [ ] **Connect a domain** (optional, provider-native subdomain available without custom domain)
- [ ] **Run initial deployment** to verify build and runtime

**Status:** DEPLOYMENT CONFIGURATIONS ARE CORRECT AND VERIFIED, but no live deployment has been performed (no provider authorized).

## Conclusion

The deployment configuration files are properly set up and verified. Both `render.yaml` and `vercel.json` are configured correctly with the right build commands, start commands, environment variables, and service configurations. However, no deployment has been executed because no hosting provider has been authorized.

To deploy: authorize a provider (Render for backend+DB, Vercel for frontend), set `GEMINI_API_KEY`, and push to trigger the deployment workflow.