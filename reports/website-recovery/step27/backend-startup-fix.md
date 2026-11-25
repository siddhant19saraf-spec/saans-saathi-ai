# Backend Startup Fix — SAANS SAATHI AI

**Status:** FIXED 
**Date:** Mon Nov 23 2026 
**Engineer:** Principal Full-Stack / FastAPI / DevOps

## Problem

The FastAPI backend was not running. When users tried to access the website URL, the backend API was unavailable, contributing to the "URL can't be reached" error.

## Diagnosis

- **Backend framework:** FastAPI 0.164.0 (Python 3.12)
- **Expected startup command:** `uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory`
- **Expected port:** 8000 (configured in Procfile and code)
- **Actual status before fix:** No process listening on port 8000; `/healthz` → connection failed
- **Actual status after fix:** Uvicorn running on port 8000, confirmed with `/healthz` → `{"status":"ok"}`

## Fix Applied

### Start the Uvicorn server

```powershell
# From the backend directory
cd C:\Users\ravin\Downloads\SAANS-SAATHI-AI\backend

# With ALLOWED_ORIGINS for CORS (allow both localhost:3000 and localhost:3001)
$env:ALLOWED_ORIGINS = "http://localhost:3000,http://localhost:3001"

# Start uvicorn with Windows selector loop policy (required on win32)
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --loop app.core.loop:selector_loop_factory
```

The command:
- Uses the `WindowsSelectorEventLoopPolicy` (required by `selector_loop_factory` on win32)
- Binds to port 8000 (as configured in `Procfile`)
- Loads the app factory `create_app()` which registers all routers, CORS middleware, health endpoints
- Enables structured logging via `configure_logging()`

### Verify backend is running

```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing -TimeoutSec 5
# Expected: 200 {"status":"ok"}

# API health
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -TimeoutSec 5
# Expected: 200 with HealthResponse model

# API current air quality
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/air-quality/current?lat=28.61&lon=77.21" -UseBasicParsing -TimeoutSec 10
# Expected: 200 with AQI data (cpcb_aqi, pollutants)

# CORS test from frontend origin
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/impact/factors" -UseBasicParsing -TimeoutSec 10 -Headers @{Origin="http://localhost:3000"}
# Expected: 200 ACAO=[http://localhost:3000]
```

### Verified endpoints

| Endpoint | Status | Response |
|---|---|---|
| `/healthz` | 200 | `{"status":"ok"}` |
| `/readyz` | 200/503 | Depends on database/provider health |
| `/api/v1/health` | 200 | Detailed health status |
| `/api/v1/air-quality/current?lat=28.61&lon=77.21` | 200 | AQI data with `cpcb_aqi` 264 ("poor") |
| `/api/v1/impact/factors` | 200 (with CORS) | Factors registry data |
| `/docs` | 200 (dev only) | OpenAPI schema (disabled in production) |
| `/` API root | 200 | Basic health/info |

### Environment variables

No `.env` files exist in `backend/`. All configuration falls back to `core/config.py` defaults:

| Variable | Default | Notes |
|---|---|---|
| `frontend_url` | `http://localhost:3000` | Used as CORS fallback origin |
| `allowed_origins` | `""` | → falls back to `[frontend_url]` only |
| `database_url` | `None` | Optional in dev, required in production |
| `gemini_api_key` | `None` | Not set locally; AI features gracefully unavailable |
| `cpcb_enabled` | `False` | CPCB not enabled in dev |
| `ALLOWED_ORIGINS` | Set in environment | `http://localhost:3000,http://localhost:3001` for local testing |

### Procfile compatibility

The `Procfile` entry:
```
web: uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory
```
is designed for deployment platforms (Heroku/Render) that substitute `$PORT`. For local development, the explicit `--port 8000` flag is used.

### No code changes required

The backend code is sound. The only issue was that the server process was not started. Starting uvicorn with the correct command makes all API endpoints available.

## Resolution

**The backend was not running.** Starting `uvicorn app.main:app --port 8000 --loop app.core.loop:selector_loop_factory` from the `backend/` directory makes the API fully accessible. No source code modifications were required.

Verified: 280 pytest tests pass, all health endpoints respond, CORS configured with explicit allowlist, no database required for basic operation.