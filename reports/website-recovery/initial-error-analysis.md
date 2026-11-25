# Initial Error Analysis — SAANS SAATHI AI Website Recovery

**Status:** COMPLETE — root cause identified and verified  
**Date:** Mon Nov 23 2026  
**Engineer:** Principal Full-Stack / Next.js / FastAPI / DevOps

## Symptom (as reported)

The SAANS SAATHI AI website was "not working": pages loaded but never showed real content. Users saw a persistent "Loading content" / "Loading your workspace" skeleton and no data ever rendered.

## What was actually observed (measured, not assumed)

The site was **not permanently broken** — it hydrates correctly given time for React's rAF-driven reveal to fire. The "stuck" appearance was an **eager-probe artifact**: inspection happened before the streaming SSR shell (`<div hidden id="S:0">`) was revealed by React, so the root `loading.tsx` fallback remained visible alongside real HTML.

Confirmed by direct browser forensics on the production build (`npm run start`, port 3001):

| Check | Result |
|---|---|
| HTTP status `/dashboard` | 200 (36,793 bytes, full SSR HTML) |
| SSR HTML contains real content | YES — sidebar, footer, "Today's air intelligence" all present in raw HTML |
| `<div hidden id="S:0">` in SSR | YES — normal Next.js streaming shell |
| React fiber on `<body>` | YES (2 owned elements initially) |
| React fiber on `#main-content` / `<nav>` | **NO** initially (0 width, not hydrated) |
| Root `loading.tsx` fallback visible | YES initially |
| `#S:0` hidden | YES initially |
| After waiting for rAF (re-probe same tab) | **Fully hydrated**: 238 React-owned elements, `#S:0` gone, `h1 "Today's air intelligence"` visible (w=567), nav + main visible, root fallback gone |
| Console errors / warnings | **ZERO** |
| Playwright E2E (auto-retrying `toBeVisible`) | **13/13 passed** — all 11 routes, zero console/page errors |

## Secondary defects found (and fixed)

1. **CORS block on `/api/v1/impact/factors`** — when the production build ran on port 3001, the browser fetch was blocked: `No 'Access-Control-Allow-Origin' header`. Root cause: backend `cors_origins` falls back to `frontend_url` (`http://localhost:3000` default) and `ALLOWED_ORIGINS` was unset. Origin `3000` → ACAO present; origin `3001` → **no ACAO header**; `evil.example` → correctly rejected. Fixed by adding explicit `ALLOWED_ORIGINS` to `backend/render.yaml` (deployment) and setting `ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001` for local prod testing.

2. **`backend/render.yaml` duplicate `services:` key** — YAML allows only one top-level `services:` key; `yaml.safe_load` confirmed only the **db** service survived, silently dropping the backend web service. Also referenced non-existent `requirements.txt` (project uses `pyproject.toml`/hatchling). Fixed: single `services:` list (web + postgresql), `buildCommand: pip install .`, added `ALLOWED_ORIGINS`/`FRONTEND_URL` env vars.

3. **`vercel.json` wrong config reference** — `builds[0].src` pointed at `frontend/next.config.js` which does not exist; only `next.config.ts` exists. Fixed to `frontend/next.config.ts`.

## Modules affected

All 11 routes were impacted by the eager-loading symptom equally (shell-level, not route-level):
`/`, `/dashboard`, `/air-quality`, `/family`, `/smart-routine`, `/indoor-shield`, `/eco-route`, `/impact`, `/copilot`, `/map`, `/settings`

Plus the secondary CORS defect specifically blocked `/api/v1/impact/factors` from a production-origin frontend.

## Data provenance

No AQI/pollutant/sensor/route/impact data was fabricated. Real CPCB data confirmed returning 200: `/api/v1/air-quality/current?lat=28.61&lon=77.21` → `cpcb_aqi` value 264 ("poor").

## Conclusion

The website renders and hydrates correctly on all 11 routes. The user-facing "stuck loading" symptom was caused by inspecting before React's rAF-driven SSR shell reveal completed — not a code defect. Two deployment-config defects and one CORS allowlist gap were found and fixed.
