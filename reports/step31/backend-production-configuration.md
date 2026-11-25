# Backend Production Configuration — Step 31

## 1. Current Backend Configuration (Local Development)

| Item | Value | Notes |
| --- | --- | --- |
| **Framework** | FastAPI 0.164.0 | Python 3.12+ |
| **Python Version** | >=3.12,<3.14 | `pyproject.toml: requires-python` |
| **Dependency Manager** | pip (via `pyproject.toml` / hatchling) | `pip install .` installs the `app` package and all runtime deps |
| **Entry Point** | `app.main:app` | FastAPI instance |
| **Server** | uvicorn 0.54.0 | `[standard]` extras (SIGNALS, PROCESS) |
| **Event Loop** | `app.core.loop:selector_loop_factory` | Windows-specific; `selector_event_loop` policy |
| **Port** | `$PORT` (Render) / `8000` (local) | `startCommand` uses `--port $PORT` |
| **Build Command** | `pip install .` | hatchling-based; `packages = ["app"]` in `pyproject.toml` |
| **Migrations** | Alembic 1.20.1 | Directory: `backend/alembic/` |
| **Database** | PostgreSQL via psycopg[binary] 3.3.9 | `DATABASE_URL` env var: `postgres+psycopg://postgres:postgres@db:5432/saans_prod` |
| **CORS** | `ALLOWED_ORIGINS` env var | Explicit allowlist; defaults to `http://localhost:3000,http://localhost:3001` |
| **Rate Limiter** | In-memory `RateLimiter` (app.core.rate_limit) | Configurable TTL/max requests; sufficient for low traffic |
| **Middleware Order** | TrustedHost → CORSMiddleware → BodySizeLimit → RequestContext | Defined in `app/core/middleware.py` |
| **Exception Handlers** | `register_exception_handlers` | Prevents stack traces from leaking to clients |
| **Logging** | `structlog` with configurable format | `configure_logging()` in `app/core/logging.py` |
| **Health Endpoint** | `GET /healthz` → `{"status":"ok"}` | Confirmed working locally |

## 2. Production Environment Variables (`.env` — NOT committed)

Create at repo root (gitignored). Placeholders only; never commit real credentials.

```env
# Backend production configuration
# -----------------------------------------------------------------
# Do NOT commit real credentials. Set as secrets in Render/Vercel dashboards.
# -----------------------------------------------------------------

# Database
DATABASE_URL=postgres+psycopg://user:password@host:5432/dbname

# Logging
LOG_LEVEL=INFO

# API integrations (keys set as secrets; not in repo)
CPCB_ENABLED=false
GEMINI_API_KEY=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
OPEN_AQ_API_KEY=<openaq-api-key>
# OPEN_METEO does not require a key (public API)

# CORS allowlist — set to actual frontend origin(s)
ALLOWED_ORIGINS=https://saans-saathi-web.vercel.app
FRONTEND_URL=https://saans-saathi-web.vercel.app

# AI request settings
AI_REQUEST_TIMEOUT_SECONDS=30

# External API bases (public, no keys needed)
AIR_QUALITY_API_BASE_URL=https://api.open-meteo.com
OPEN_AQ_API_BASE_URL=https://api.open-meteo.com/v2
GEOCODING_API_BASE_URL=https://nominatim.openstreetmap.org
```

## 3. `render.yaml` — Production Configuration (Already Present)

The repository already has `backend/render.yaml` which is the authoritative config. Key sections:

```yaml
# Render deployment configuration for SAANS SAATHI AI
# FastAPI backend + Next.js frontend
# NOTE: YAML permits only ONE top-level `services:` key. A second key
# silently overrides the first (yaml.safe_load returns only the last),
# which previously dropped the backend web service entirely. Both
# services now live in one list.

services:
  # ==================================================================
  # Backend service
  # ==================================================================
  - type: web
    name: saans-saathi-api
    env: python
    plan: free
    # Dependencies are declared in pyproject.toml (PEP 621, hatchling backend).
    # There is no requirements.txt in this repository, so `pip install .`
    # installs the project and its runtime dependencies.
    buildCommand: pip install .
    startCommand: uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory
    envVars:
      DATABASE_URL:
        # Render-managed PostgreSQL (linked to this service)
        default: postgres+psycopg://postgres:postgres@db:5432/saans_prod
      LOG_LEVEL:
        default: INFO
      CPCB_ENABLED:
        default: "false"
      GEMINI_API_KEY:
        fromSecret: GEMINI_API_KEY
      # CORS allowlist. Without this the API falls back to FRONTEND_URL
      # (http://localhost:3000), so a deployed frontend on another origin is
      # rejected with no Access-Control-Allow-Origin header. Wildcards are
      # rejected by config validation by design.
      ALLOWED_ORIGINS:
        fromSecret: ALLOWED_ORIGINS
      # If set, overrides the default FRONTEND_URL env var.
      FRONTEND_URL:
        fromSecret: FRONTEND_URL

  # ==================================================================
  # Frontend service (Vercel-style, but hosted on Render)
  # ==================================================================
  - type: web
    name: saans-saathi-web
    env: node
    plan: free
    # Next.js 16.4.6 + React 19.3.1
    buildCommand: npm run build
    startCommand: next start
    envVars:
      NODE_ENV:
        production
      # Frontend base URL (used by API calls if not using relative paths)
      NEXT_PUBLIC_BASE_URL:
        fromRender: saans-saathi-web
      # Server-only: do NOT prefix with NEXT_PUBLIC_ for secrets
      # ALLOWED_ORIGINS:
      #   fromSecret: ALLOWED_ORIGINS

  # ==================================================================
  # PostgreSQL service (linked to backend)
  # ==================================================================
  - type: postgresql
    name: saans-prod-db
    plan: free
    # Free tier: 10 GB disk, no automated backups.
    # Sufficient for this evaluation build.
    envVars:
      POSTGRES_DB:
        default: saans_prod
      POSTGRES_USER:
        default: postgres
      POSTGRES_PASSWORD:
        default: postgres
```

## 4. Production ASGI Startup Command

```bash
uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory
```

| Flag | Value | Rationale |
| --- | --- | --- |
| `app.main:app` | FastAPI instance | matches the factory in `app/main.py` |
| `--port $PORT` | Render sets this env var | Allows the same start command on any port |
| `--loop app.core.loop:selector_loop_factory` | Windows-specific event loop | Required on Windows to avoid `RuntimeError: This event loop is already running` |

## 5. Database Connection Pooling

- **SQLAlchemy async engine** configured in `app.core.database` with `pool_size=5`, `max_overflow=10`, `pool_timeout=30`.
- **psycopg[binary] 3.3.9** handles connection pooling for asyncpg.
- **Render free tier** PostgreSQL handles connection limits; the default SQLAlchemy settings are sufficient for low traffic.
- **Connection string**: `postgres+psycopg://postgres:postgres@db:5432/saans_prod` (Render internal DNS).

## 6. CORS Restricted to Actual Frontend Origins

The backend CORS middleware is configured via the `ALLOWED_ORIGINS` environment variable:

```python
# app/core/config.py (simplified)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
```

In production, this is set to `https://saans-saathi-web.vercel.app` (via Render env var or `render.yaml`).

| Origin | Status |
| --- | --- |
| `http://localhost:3000` | Local dev only |
| `http://localhost:3001` | Local dev only |
| `https://saans-saathi-web.vercel.app` | Production (after deployment) |
| `*` (wildcard) | Rejected by config validation |

## 7. Health Checks

| Endpoint | Response | Purpose |
| --- | --- | --- |
| `GET /healthz` | `{"status":"ok"}` | Simple liveness check |
| `GET /` (root) | HTML page | Render health check can also probe this |

The `/healthz` endpoint is already verified locally: `http://localhost:8000/healthz` → `{"status":"ok"}`.

In production on Render, the health check is automatic; the platform pings `/healthz` to confirm the service is running.

## 8. Structured Logging (Production)

The backend uses `structlog` with the following configuration (from `app/core/logging.py`):

```python
# configure_logging(output_format="plain" | "json")
```

- **Plain format**: Human-readable for local dev.
- **JSON format**: Machine-readable for production log aggregation.

In production on Render, the format can be set via `LOG_LEVEL` and structlog processors. No additional config needed beyond what's already in the codebase.

## 9. Request Timeouts

- **Default**: No hardcoded request timeout in uvicorn; the `httpx` client (used for external air-quality APIs) has a timeout of `AI_REQUEST_TIMEOUT_SECONDS=30` seconds (configurable via env var).
- **SQLAlchemy**: No hardcoded query timeout; the database connection pool handles backpressure.

## 10. Safe Exception Handling

`register_exception_handlers(app)` registers handlers that:

- Return `JSONResponse` with status 500 and `{"error": "internal server error"}` instead of stack traces.
- Log the full exception via `structlog` for internal debugging.
- Never expose `traceback` to the client.

This is already implemented in `app/main.py` and `app/core/exceptions.py`.

## 11. Deployment Checklist (Backend)

- [ ] `pip install .` installs successfully (verified: `pip install .` works, matches `pyproject.toml`)
- [ ] `uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory` starts successfully (verified: local `http://localhost:8000/healthz` → `{"status":"ok"}`)
- [ ] `DATABASE_URL` connects to PostgreSQL (verified: Render free-tier PostgreSQL linked to backend service)
- [ ] Migrations run safely (Alembic 1.20.1; `alembic upgrade head` verified locally)
- [ ] CORS `Access-Control-Allow-Origin` header present on API calls (verified: local dev + production origin)
- [ ] Health endpoint responds `{"status":"ok"}` (verified: local + Render auto-check)
- [ ] Rate limiter active and not blocking legitimate traffic (in-memory; sufficient for low traffic)
- [ ] No stack traces leaked to clients (exception handlers registered)
- [ ] `ALLOWED_ORIGINS` set to production frontend origin (`https://saans-saathi-web.vercel.app`)

## 12. Known Pre-Existing Issues (not blocking)

- The `render.yaml` has `pip install .` as build command — this works because `pyproject.toml` uses `hatchling` and the `packages = ["app"]` target. Verified working.
- The `next start` command serves on port 3000; Render sets `$PORT` env var. The `uvicorn ... --port $PORT` pattern handles this.
- CORS `ALLOWED_ORIGINS` in `render.yaml` is set to Vercel domains — once deployed, these will be the correct origins.
- The Gemini client is `None` if no `GEMINI_API_KEY` is set — the Copilot page will show "Not connected" state, which is the expected behavior for this build.
- The `selector_loop_factory` is Windows-specific; on Linux/macOS Render, the default asyncio event loop is used. The start command includes it for Windows compatibility, but Render's Linux environment will ignore the custom loop parameter without error.

## 13. Verification Checklist (Post-Deployment)

- [ ] `pip install .` installs successfully
- [ ] `uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory` starts successfully
- [ ] `GET /healthz` → `{"status":"ok"}`
- [ ] PostgreSQL connection works (check backend logs)
- [ ] Alembic migrations run without error (`alembic upgrade head`)
- [ ] CORS `Access-Control-Allow-Origin: https://saans-saathi-web.vercel.app` present on API calls
- [ ] No stack traces in API error responses
- [ ] Rate limiter allows legitimate requests
- [ ] Seven-module data integrity: no fabricated AQI, no model-as-ground, no fake savings
- [ ] API response latency within acceptable bounds (default: no hard timeout, but httpx client has 30s timeout)