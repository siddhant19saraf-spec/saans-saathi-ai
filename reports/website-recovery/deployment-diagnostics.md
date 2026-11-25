# Deployment Diagnostics — SAANS SAATHI AI Website Recovery

**Status:** COMPLETE — both deployment configs fixed and verified  
**Date:** Mon Nov 23 2026  
**Engineer:** Principal DevOps

## No live deployment confirmed

- Only `.github/workflows/quality-checks.yml` exists (CI quality gates).
- **No deploy workflow** and **no live URL** confirmed.
- No deployment provider (Render/Vercel/other) has been authorized or connected.
- Per constraints: no deploy or push performed without authorization; existing GitHub repo and branch (`main`, HEAD `0a22cc4`) preserved.

## Defect 1: `backend/render.yaml` — duplicate `services:` key

**Confirmed via `yaml.safe_load`:** The file had two top-level `services:` keys. YAML permits only one; the parser returned only the **last** (`db` postgresql), silently dropping the `saans-saathi-api` web service. The backend would never have been deployed.

Also: `buildCommand: pip install -r requirements.txt` — `requirements.txt` does **not** exist. Dependencies are declared in `pyproject.toml` (PEP 621, hatchling build backend). This command would fail at build time.

**Before (defective):**
```yaml
services:
  - type: web
    name: saans-saathi-api
    ...
    buildCommand: pip install -r requirements.txt   # file does not exist
    ...
services:                                            # duplicate key — silently overrides above
  - type: postgresql
    name: db
    ...
```

**After (fixed):**
```yaml
services:
  - type: web
    name: saans-saathi-api
    env: python
    plan: free
    buildCommand: pip install .                      # installs pyproject.toml deps
    startCommand: uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory
    envVars:
      DATABASE_URL: postgres+psycopg://postgres:postgres@db:5432/saans_prod
      LOG_LEVEL: INFO
      CPCB_ENABLED: "false"
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      ALLOWED_ORIGINS: https://saans-saathi-web.vercel.app,https://saans-saathi-api.vercel.app
      FRONTEND_URL: https://saans-saathi-web.vercel.app
  - type: postgresql
    name: db
    plan: free
    disk: 10
```

**Verified:** `yaml.safe_load` now returns `keys: ['services']`, `count: 2`, `names: ['saans-saathi-api', 'db']`, `types: ['web', 'postgresql']`, `build: pip install .`. Exactly one top-level `services:` key.

## Defect 2: `vercel.json` — stale Next.js config reference

**Before (defective):**
```json
{
  "version": 2,
  "builds": [
    { "src": "frontend/next.config.js", "use": "@vercel/next-build" }
  ],
  ...
}
```
`frontend/next.config.js` does **not** exist; only `frontend/next.config.ts` exists. The Vercel build would reference a missing file.

**After (fixed):**
```json
{ "src": "frontend/next.config.ts", "use": "@vercel/next-build" }
```

**Verified:** `node -e "require('./vercel.json")` → valid JSON; `builds[0].src === "frontend/next.config.ts"`; `fs.existsSync("frontend/next.config.ts") === true`.

## Build & start commands verified locally

| Service | Command | Result |
|---|---|---|
| Backend | `uvicorn app.main:app --port 8000 --loop app.core.loop:selector_loop_factory` | Starts clean, `/healthz` 200 |
| Frontend dev | `npm run dev` (Next.js 16.4.6 Turbopack) | Ready, `/dashboard` 200 |
| Frontend prod | `npm run build` → `npm run start` (port 3001) | Build PASS (11 static routes + `_not-found`), server ready, `/dashboard` 200 |

## CORS for deployment

`render.yaml` now sets `ALLOWED_ORIGINS` to the two Vercel origins and `FRONTEND_URL` to the web origin, so the production frontend can call the production API. Wildcards are rejected by config validation (`_validate_allowed_origins` raises on `"*"`).

## Remaining deployment items (not part of this emergency fix; require authorization)

1. Connect a deployment provider (Render for backend, Vercel for frontend).
2. Set `GEMINI_API_KEY`, `DATABASE_URL`, `ALLOWED_ORIGINS`, `FRONTEND_URL` in the provider.
3. Add a deploy workflow (`.github/workflows/deploy.yml`) or use provider auto-deploy from `main`.
4. Confirm a live URL and run smoke tests against it.

Per constraints: none of the above was performed without authorization.

## Conclusion

Both defective deployment configs were found, fixed, and verified by parsing. `render.yaml` now deploys both backend + database with the correct build command; `vercel.json` now references the existing `next.config.ts`. No deployment was executed (no provider confirmed, no authorization).
