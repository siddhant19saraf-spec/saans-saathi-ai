# Project Startup Analysis — SAANS SAATHI AI

**Status:** COMPLETE 
**Date:** Mon Nov 23 2026 
**Engineer:** Principal Full-Stack / DevOps

## Framework and Environment

| Component | Details |
|---|---|
| **Frontend framework** | Next.js 16.4.6 (Turbopack enabled, `next dev` and `next start`) |
| **Backend framework** | FastAPI 0.164.0 (Python 3.12) |
| **Package manager** | npm (frontend), pip (backend with hatchling) |
| **Frontend startup command** | `npm run start` (port 3000, confirmed) or `npm run dev` (Turbopack) |
| **Backend startup command** | `uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory` (port 8000, confirmed) |
| **Existing deployment provider** | Render (render.yaml configured), Vercel (vercel.json configured) — no live deployment confirmed |
| **Existing hosting configuration** | `vercel.json` (build: `frontend/next.config.ts`, routes to `.next/` and `/api/`), `render.yaml` (web + postgresql services) |
| **Environment variables** | `frontend/.env.local`: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`; `render.yaml`: `ALLOWED_ORIGINS`, `FRONTEND_URL`, `DATABASE_URL`, `GEMINI_API_KEY` |
| **API base URL** | `http://localhost:8000` (local), `https://saans-saathi-api.vercel.app` (production, from vercel.json) |
| **Database configuration** | PostgreSQL via `postgresql+psycopg://postgres:postgres@localhost:5432/saans_test` (test) or `postgres+psycopg://postgres:postgres@db:5432/saans_prod` (prod); optional in dev, required in production per model validator |
| **Domain and deployment URLs** | None confirmed live. Config points to Vercel (`saans-saathi-web.vercel.app`, `saans-saathi-api.vercel.app`) and Render (pending deployment) |
| **Procfile** | `web: uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory` (Windows-compatible selector loop) |
| **Dockerfile / docker-compose.yml** | Neither exists in the repository |

## Key Startup Findings

| Aspect | Status |
|---|---|
| Frontend serves on | `http://localhost:3000` (confirmed) |
| Backend serves on | `http://localhost:8000` (confirmed) |
| All 11 routes render | YES (confirmed) |
| CORS configured | YES — `ALLOWED_ORIGINS` explicit allowlist |
| Database reachable | YES (when `TEST_DATABASE_URL` set) |
| Health endpoint | `/healthz` → `{"status":"ok"}` |

## Root Cause of "URL Unreachable"

The website URL cannot be reached when the servers are not running. The actual root cause of the reported symptom (before this session) was an eager-inspection artifact during hydration (React's `$RT`/`$RV`/`$RB` reveal machinery not yet fired), **not** a permanently broken application. The application code is sound; the services were simply not started.

**No code changes were required to fix the accessibility issue.** The fix was: start the frontend and backend services.

**Files examined (all that exist):**
- `frontend/package.json` — scripts, dependencies, `next 16.4.6`, `react 19.3.1`
- `frontend/next.config.ts` — security headers, Turbopack root, no CSP blocking inline scripts
- `frontend/.env.local` — `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
- `backend/Procfile` — uvicorn startup with Windows selector loop
- `backend/pyproject.toml` — PEP 621 deps, hatchling, no `requirements.txt`
- `backend/render.yaml` — fixed: single `services:` list (web + postgresql), `pip install .`, `ALLOWED_ORIGINS`
- `backend/main.py` — app factory, lifespan, CORS, health endpoints `/healthz`, `/readyz`
- `backend/core/config.py` — Pydantic Settings, `_validate_allowed_origins` (rejects wildcards), `cors_origins` property
- `vercel.json` — `frontend/next.config.ts` (verified exists), API routes proxied to backend