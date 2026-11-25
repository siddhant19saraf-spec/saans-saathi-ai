# Backend Recovery — SAANS SAATHI AI Website

**Status:** COMPLETE — backend healthy; one CORS allowlist defect fixed  
**Date:** Mon Nov 23 2026  
**Engineer:** Principal Full-Stack / FastAPI / DevOps

## Backend runtime state

- Entrypoint: `backend/Procfile` — `web: uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory`
- Runs on Windows with `WindowsSelectorEventLoopPolicy` (required by `selector_loop_factory` on win32).
- `DATABASE_URL` optional in dev; logs `database_not_configured` (expected).
- Health endpoints all **200**: `/healthz`, `/readyz`, `/api/v1/health`, `/docs`, `/api/v1/meta`
- Real AQI data **200**: `/api/v1/air-quality/current?lat=28.61&lon=77.21` → `cpcb_aqi` 264 ("poor")
- `/api/v1/ecoroute/providers/health` **200**
- Pytest: **280 passed, 0 failed** (7m39s, full run with `TEST_DATABASE_URL` set)

## Genuine defect fixed: CORS allowlist gap

`backend/app/core/config.py`:
```python
frontend_url: str = "http://localhost:3000"   # default
allowed_origins: str = ""                      # unset in dev (no .env file)
...
@property
def cors_origins(self) -> list[str]:
    origins = [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
    return origins or [self.frontend_url]      # -> ["http://localhost:3000"] only
```

Direct probe against running backend (:8000) with `Origin` header:

| Origin | `Access-Control-Allow-Origin` | Result |
|---|---|---|
| `http://localhost:3000` | `http://localhost:3000` | ✅ allowed |
| `http://localhost:3001` | **(absent)** | ❌ fetch blocked by CORS |
| `http://evil.example` | **(absent)** | ✅ correctly rejected (no wildcard) |

Validation in `_validate_allowed_origins` rejects wildcards (`*`) and requires absolute http(s) origins — so the safe fix is an explicit allowlist, not a wildcard.

Fix applied to `backend/render.yaml` (deployment):
```yaml
envVars:
  ALLOWED_ORIGINS: https://saans-saathi-web.vercel.app,https://saans-saathi-api.vercel.app
  FRONTEND_URL: https://saans-saathi-web.vercel.app
```
For local production-build testing, `ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001` was set in the environment.

## Deployment config fix: `backend/render.yaml`

Problems confirmed via `yaml.safe_load`:
1. **Duplicate top-level `services:` key** — only one `services:` key is permitted; the load returned only the `db` postgresql service, **silently dropping the backend web service**.
2. `buildCommand: pip install -r requirements.txt` — `requirements.txt` does not exist; dependencies are declared in `pyproject.toml` (hatchling build backend).

Fix: single `services:` list with both `saans-saathi-api` (web) and `db` (postgresql); `buildCommand: pip install .`; added `ALLOWED_ORIGINS`/`FRONTEND_URL` env vars. Verified: parses to 2 services, build command correct.

## Backend route inventory

Unversioned (main.py): `/healthz`, `/readyz`

Versioned under `/api/v1`:
- `air.py`: `/current`, `/forecast`, `/history`, `/providers/health`, `/stations`
- `copilot.py`: `/chat`, `/tool-request`
- `ecoroute.py`: `/calculate-emissions`, `/compare`, `/journeys`, `/providers/health`
- `family.py`: `/preferences`, `/profile`, `/profile/{recommendation_id}`, `/recommendations`, `/recommendations/generate`
- `health.py`: `/health`
- `household.py`: `/locations`, `/locations/{location_id}`, `/members`, `/members/{member_id}`, `/preferences`
- `impact.py`: `/activities`, `/baseline-savings`, `/factors`, `/goals`, `/goals/{goal_id}`, `/methodology`, `/summary`, `/trends`
- `indoor.py`: `/assess`, `/assessments`, `/assessments/{assessment_id}`, `/assessments/{assessment_id}/explain`, `/assessments/{assessment_id}/refresh`, `/overview`, `/recommendations`, `/recommendations/{recommendation_id}/complete|events|reopen|reschedule`, `/sensors`, `/sensors/{sensor_id}`, `/sensors/{sensor_id}/readings`
- `locations.py`: `/search`
- `meta.py`: `/meta`
- `routines.py`: `/activities`, `/activities/{activity_id}`, `/generate`, `/history`, `/{routine_id}`, `/{routine_id}/activities/{activity_id}`, `/{routine_id}/items/{block_id}`, `/{routine_id}/replan`
- `sessions.py`: `/me`, `/me/consent`

No data fabrication: all AQI/pollutant/sensor/route/impact values come from real providers or deterministic rules; unavailable surfaces return 503 problem documents rather than invented measurements.

## Verification results

| Suite | Result |
|---|---|
| Pytest (`--cov=app`) | 280 passed, 0 failed (7m39s); 0 skipped when `TEST_DATABASE_URL` set |
| Coverage | TOTAL 78.86% — `FAIL Required test coverage of 80.0% not reached` (pre-existing, documented, not suppressed) |
| Ruff | clean (exit 0) |
| Black | clean (exit 0) |
| MyPy `app` | clean (exit 0) |
| Bandit | exit 0 |
| `uvicorn` import/start | `IMPORT_OK`, starts clean |

## Test database

`TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/saans_test` — verified reachable (`SELECT 1` OK). Without it set, 97 database-backed tests are skipped (documented behavior).

## Conclusion

Backend is healthy: imports clean, uvicorn starts, all health endpoints 200, real AQI data returns 200, 280/280 tests pass. One genuine defect (CORS allowlist too narrow for production frontend origin) and two deployment-config defects (render.yaml duplicate key + missing requirements.txt) were found and fixed.
