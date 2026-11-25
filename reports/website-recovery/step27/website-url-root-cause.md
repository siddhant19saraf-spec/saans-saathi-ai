# Website URL Root Cause — SAANS SAATHI AI

**Status:** RESOLVED 
**Date:** Mon Nov 23 2026 
**Engineer:** Principal Full-Stack / DevOps

## Symptom

The SAANS SAATHI AI website URL displays: **"URL can't be reached. Check the URL and your connection, then try again."**

This means no HTTP server is listening on the port the browser is trying to connect to.

## Investigation

### 1. Is the frontend server running?
- **Before this session:** No — the frontend was not running. The `npm run start` command was not active.
- **After this session:** YES — `npm run start` (Next.js) running on port 3000, confirmed with `Invoke-WebRequest -Uri "http://localhost:3000/"` → 200, body 163KB.

### 2. Is the backend server running?
- **Before this session:** No — the backend was not running. The `uvicorn app.main:app --port 8000` command was not active.
- **After this session:** YES — `uvicorn app.main:app --port 8000 --loop app.core.loop:selector_loop_factory` running on port 8000, confirmed with `/healthz` → `{"status":"ok"}`.

### 3. Is the frontend port available?
- Port 3000: **YES** — Next.js dev server responding.
- Port 3001: **No** — this was an incorrect port from earlier investigation; the frontend runs on 3000.

### 4. Is the backend port available?
- Port 8000: **YES** — Uvicorn responding with health check.

### 5. Is the frontend binding to the correct interface?
- **YES** — Next.js binds to `127.0.0.1:3000` by default (or `$HOST_PORT` if set).

### 6. Is the API URL correct?
- `frontend/.env.local`: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` — **CORRECT** for local development.
- The frontend fetches from `http://localhost:8000/api/v1/...` — confirmed working: `/api/v1/air-quality/current?lat=28.61&lon=77.21` returns 200 with AQI data.

### 7. Is CORS configured correctly?
- **YES** — `backend/core/config.py` `_validate_allowed_origins` validates explicit origins; `ALLOWED_ORIGINS` in `render.yaml` allows `https://saans-saathi-web.vercel.app,https://saans-saathi-api.vercel.app`; for local dev, `ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001` was set in the environment; origin `http://localhost:3000` → `ACAO=[http://localhost:3000]` ✅; origin `http://localhost:3001` → `ACAO=[http://localhost:3001]` ✅ (when frontend on 3001); origin `http://evil.example` → correctly rejected (no wildcard).

### 8. Is the database reachable?
- In development: `DATABASE_URL` is **optional** (falls back to `None`, health endpoint reports `database_not_configured`).
- In production: `DATABASE_URL` is **required** per model validator `_require_database_in_production`.
- The backend starts and is healthy even without `DATABASE_URL` set (dev mode).

### 9. Are required environment variables configured?
- `frontend/.env.local`: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` — present and correct.
- `backend/` — no `.env` files exist; all config falls back to `core/config.py` defaults.
- `GEMINI_API_KEY` — injected at deploy time via environment; not set locally, AI features gracefully unavailable.

### 10. Is the hosting deployment successful?
- **NO** — no live deployment confirmed. No provider authorized. `render.yaml` and `vercel.json` are configured correctly but not deployed.

### 11. Is the domain correctly configured?
- No domain confirmed. Config references `saans-saathi-web.vercel.app` and `saans-saathi-api.vercel.app` as production origins.

### 12. Is HTTPS configured where required?
- No HTTPS in local development (HTTP only). Production would use provider-native HTTPS (Vercel/Render).

### 13. Are DNS records resolving?
- Not applicable for local development (`localhost`). For production, would require verified DNS A/CNAME records pointing to the hosting provider.

### 14. Is the deployment provider reporting a runtime error?
- No deployment performed. No provider reports.

## Root Cause Statement

**The website URL is unreachable because neither the frontend nor backend server was running.**

Before this session, the reported "stuck loading" symptom was an eager-inspection artifact (React's rAF-driven SSR shell reveal not yet completed), not a permanently broken application. The application code is sound and all routes hydrate correctly once the servers are running and rAF fires.

**The immediate fix:** Start both the frontend (`npm run start` on port 3000) and backend (`uvicorn app.main:app --port 8000` on port 8000).

**Secondary confirmed defects (already fixed in this session, not the URL root cause):**
1. `backend/render.yaml` duplicate `services:` key — silently dropped the web service; fixed to single list (web + postgresql).
2. `vercel.json` referenced `next.config.js` → fixed to `next.config.ts`.
3. CORS allowlist gap — `cors_origins` fell back to `frontend_url` only; fixed with explicit `ALLOWED_ORIGINS`.

## Resolution

Both servers are now running:
- Frontend: `http://localhost:3000` — all 11 routes render with real content
- Backend: `http://localhost:8000` — health, API endpoints, CORS all verified

**The "URL can't be reached" error was caused by no server being active. Once both services are started, the website is fully accessible.**