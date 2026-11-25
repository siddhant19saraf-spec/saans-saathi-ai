# Production Architecture — Step 31

## 1. Current Architecture

The application consists of three primary components:

| Component | Technology | Port | Command |
| --- | --- | --- | --- |
| **Frontend** | Next.js 16.4.6, React 19.3.1 | 3000 | `next start` |
| **Backend** | FastAPI 0.164.0, Python 3.12+ | 8000 | `uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory` |
| **Database** | PostgreSQL (via Render free tier) | — | — |

### Frontend Details

- **Framework**: Next.js 16.4.6 (App Router)
- **Routing**: Route-group `app` contains the 11 functional routes + `/` marketing landing page
- **Data fetching**: `useAirCurrent`, `useLocations`, `useRoutineActivities`, `useImpactActivities`, `useIndoorChecklist`, `useEcoPreferences`, `useNotificationPreferences`, `useFamilyWorkspace`
- **State management**: `useSyncExternalStore` for motion preference and sidebar collapse persistence
- **Stores**: localStorage for locations, routine activities, impact activities, indoor checklist, notification preferences, eco preferences
- **Build**: `next build` → static + server components → `next start`
- **CSS**: Tailwind CSS v4 via `@tailwindcss/postcss`; tokens in `globals.css @theme`
- **No `tailwind.config.ts`** — all tokens live in the `@theme` block of `globals.css`

### Backend Details

- **Framework**: FastAPI 0.164.0
- **ORM**: SQLAlchemy 2.1.9 with async support
- **Migrations**: Alembic 1.20.1
- **Database**: PostgreSQL via psycopg[binary] 3.3.9
- **HTTP client**: httpx 0.28.1 for external air-quality APIs
- **Background loop**: `app.core.loop:selector_loop_factory` (Windows-selector-event-loop policy)
- **CORS**: `ALLOWED_ORIGINS` allowlist via environment variable
- **Rate limiting**: In-memory RateLimiter
- **Logging**: structlog with JSON or plain format config
- **Exception handling**: Custom exception handlers registerd via `register_exception_handlers`
- **Middleware**: TrustedHost, CORSMiddleware, BodySizeLimit, RequestContext

### Database Details

- **PostgreSQL** via Render free tier
- **Alembic migration directory**: `backend/alembic/`
- **Connection**: `postgres+psycopg://postgres:postgres@db:5432/saans_prod` (Render-managed)
- **Schema**: Tables for users, locations, activities, settings, etc. (standard FastAPI SQLAlchemy layout)

### Infrastructure

- **Deployment config**: `backend/render.yaml` — combined backend + frontend + PostgreSQL in one service list
- **No Dockerfile** present — Render builds from source
- **No GitHub Actions** — manual deployment or Render auto-deploy from git
- **No secrets in repo** — `GEMINI_API_KEY`, `OPEN_AQ_API_KEY` etc. via env vars
- **Procfile**: `uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory`

## 2. Proposed Hosting Architecture

| Layer | Provider | Rationale |
| --- | --- | --- |
| **Frontend** | **Vercel** | - Native Next.js support (auto-detects `next start` or serverless functions)<br>- HTTPS auto-provisioned<br>- Edge network with global CDN<br>- Free tier sufficient for low traffic<br>- `vercel.json` already points to `frontend/next.config.ts` (per render.yaml notes)<br>- `npm run build` outputs serverless-compatible output |
| **Backend** | **Render** | - Existing `render.yaml` config<br>- Free tier includes PostgreSQL + Python/Node services<br>- HTTPS auto-provisioned<br>- Persistent disk for PostgreSQL (10GB free)<br>- Auto-deploy from git<br>- `pip install .` build command matches pyproject.toml<br>- `uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory` start command matches<br>- CORS `ALLOWED_ORIGINS` already configured for Vercel domains |
| **Database** | **Render PostgreSQL** (linked to Render backend service) | - Same provider as backend → simplified networking<br>- Free tier 10GB disk<br>- Managed backups not available on free, but sufficient for this build<br>- Connection string already in `render.yaml` envVars<br>- No additional cost if staying on free tier |

### Architecture Diagram

```
+---------------------+       HTTPS       +---------------------+
|   Vercel (Frontend) |  <-------------> |   Render (Backend)  |
|  - Next.js 16.4.6   |  HTTPS + CDN    |  - FastAPI 0.164.0  |
|  - / route           |-----------------|  - SQLAlchemy ORM   |
|  - /dashboard etc.   |               |  - Alembic migrations|
|  - Static assets    |               |  - psycopg + PostgreSQL|
|  - API routes       |               |  - Rate limiter      |
+---------------------+               +---------------------+
          |                           |
          |                           v
          |                    +---------------------+
          |                    |  PostgreSQL (free)  |
          |                    |  10GB disk, managed |
          |                    +---------------------+
```

### Why This Combination

1. **Next.js + Vercel**: Zero-configuration deployment. `next build` + `next start` semantics are native to Vercel. The existing `package.json` scripts (`dev`, `build`, `start`) map directly. No need to eject or eject to a custom server.

2. **FastAPI + Render**: The existing `render.yaml` already configures this exactly. No changes needed to the backend code or `render.yaml` beyond what's already there. The free tier is sufficient for the expected low traffic of this build.

3. **PostgreSQL + Render**: Staying on the same provider eliminates cross-provider networking complexity. The `DATABASE_URL` env var is already set in `render.yaml`. No need to manage a separate RDS instance.

4. **No paid infrastructure**: All three components have free-tier availability that covers the expected usage of this evaluation build.

5. **HTTPS everywhere**: Both Vercel and Render provision automatic HTTPS certificates. No manual cert management needed.

### Deployment Cost (Free Tier)

| Component | Cost | Notes |
| --- | --- | --- |
| Vercel (Frontend) | $0 | Free tier: 100GB bandwidth, 1 GB serverless function minutes per day, enough for this build |
| Render (Backend + PostgreSQL) | $0 | Free tier: 750 hours/month per service, 10GB PostgreSQL disk. Both services combined stay under 750 hrs if always-on is not required, or if the app sleeps when not in use. |
| **Total** | **$0** | All-free-tier deployment possible. |

### If Paid tiers were needed

- Vercel Pro: ~$20/mo for custom domains, increased bandwidth, preview deployments.
- Render Starter: $7/mo per service for always-on, custom domains, higher bandwidth.
- PostgreSQL paid plan: $7–$15/mo for automated backups, larger disk.

But for this Step 31 exercise, the free tier should be sufficient.

## 3. Migration Path from Current Local Setup

1. **Push repository** to a GitHub repository (GitHub free tier)
2. **Vercel**: Connect the repo, set framework to "Next.js", the root directory to `/` (or `frontend/` depending on repo structure), and deploy. Vercel will automatically run `npm run build` and `npm run start`.
3. **Render**: New web service, Python, set build command to `pip install .`, start command to `uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory`. Add PostgreSQL service, link to the web service. Set env vars from `render.yaml`.
4. **Environment variables**: Ensure `GEMINI_API_KEY`, `OPEN_AQ_API_KEY`, `CPCB_API_KEY` etc. are set as secrets in Render/Vercel dashboards (NOT in repo).
5. **Domain**: Vercel provides a `*.vercel.app` domain; custom domains can be added later.
6. **Verify**: Check `/healthz` → `{"status":"ok"}`, check all 11 routes, run the seven-module workflows.

## 4. Production Configuration Items

### Frontend (.env.production — not committed, placeholders only)

```env
# Frontend production configuration
NEXT_PUBLIC_BASE_URL=https://saans-saathi-web.vercel.app
# The following are NOT prefixed with NEXT_PUBLIC_ as they are server-only:
# API base is configured in next.config.ts or via environment replacement
```

### Backend (.env — not committed)

```env
# Backend production configuration
DATABASE_URL=postgres+psycopg://user:password@host:5432/dbname
LOG_LEVEL=INFO
CPCB_ENABLED=false
GEMINI_API_KEY=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
OPEN_AQ_API_KEY=<openaq-api-key>
# CORS allowlist — set to actual frontend origin(s)
ALLOWED_ORIGINS=https://saans-saathi-web.vercel.app
FRONTEND_URL=https://saans-saathi-web.vercel.app
# AI request settings
AI_REQUEST_TIMEOUT_SECONDS=30
# Open-Meteo / OpenAQ / OpenAI settings
AIR_QUALITY_API_BASE_URL=https://api.open-meteo.com
OPEN_AQ_API_BASE_URL=https://api.open-meteo.com/v2
GEOCODING_API_BASE_URL=https://nominatim.openstreetmap.org
```

### Database (managed by Render)

No manual config needed beyond the `DATABASE_URL` env var in `render.yaml`.

## 5. Security Checklist

- [ ] HTTPS enabled by default (Vercel + Render)
- [ ] No `NEXT_PUBLIC_` env vars containing secrets (per the important rules)
- [ ] CORS restricted to actual frontend origins via `ALLOWED_ORIGINS`
- [ ] Gemini API key never in browser code — server-side only (already documented: "No Gemini key in browser code — server-side only")
- [ ] OpenAQ API key server-side only (same)
- [ ] Rate limiting active (in-memory RateLimiter; sufficient for low traffic)
- [ ] Body size limit middleware configured (`config.request_max_bytes`)
- [ ] Exception handlers prevent stack traces from leaking to clients
- [ ] SQL injection protection via SQLAlchemy parameterized queries (already used)
- [ ] Input validation via Pydantic schemas (already used)
- [ ] Security headers via FastAPI middleware (TrustedHost, CORSMiddleware already configured)
- [ ] No credential exposure in logs (structlog configuration check needed)
- [ ] API error responses don't expose stack traces (custom exception handlers)

## 6. Deployment Execution Steps

1. Push repository to GitHub (private repo)
2. **Vercel**: New project → Import GitHub repo → Framework: Next.js → Root Directory: leave blank (repo root contains `frontend/` subdirectory, but the `package.json` is at root, so Vercel auto-detects) → Deploy
3. **Render**: New service → Web Service → Python → Set build/start commands from `render.yaml` → Add PostgreSQL service → Link to web service → Set env vars from `render.yaml` → Deploy
4. **Set secrets**: In Render dashboard, set `GEMINI_API_KEY`, `OPEN_AQ_API_KEY`, `OPEN_METEO_API_KEY` (if needed) as environment variables
5. **Verify**: `https://saans-saathi-web.vercel.app/healthz` → check 11 routes, seven modules
6. **Test**: Run the seven-module workflows, verify mobile responsiveness, check console for errors

## 7. Known Pre-Existing Issues (not blocking)

- The `render.yaml` has `pip install .` as build command — this works because `pyproject.toml` uses `hatchling` and the `packages = ["app"]` target. Verified working.
- The `next start` command serves on port 3000; Render sets `$PORT` env var. The `uvicorn ... --port $PORT` pattern handles this.
- CORS `ALLOWED_ORIGINS` in `render.yaml` is set to Vercel domains — once deployed, these will be the correct origins.
- The Gemini client is `None` if no `GEMINI_API_KEY` is set — the Copilot page will show "Not connected" state, which is the expected behavior for this build.

## 8. Verification Checklist (Post-Deployment)

- [ ] Frontend URL responds with 200
- [ ] `/healthz` → `{"status":"ok"}`
- [ ] All 11 routes have correct h1 headings
- [ ] Seven modules accessible (Air Intelligence, Family Intelligence, SmartRoutine, IndoorShield, EcoRoute, Impact, Copilot)
- [ ] Mobile navigation drawer works
- [ ] No console errors beyond expected Next.js runtime messages
- [ ] CORS `Access-Control-Allow-Origin` header present on API calls
- [ ] PostgreSQL connection works (check backend logs)
- [ ] Seven-module data integrity: no fabricated AQI, no model-as-ground, no fake savings
- [ ] Responsiveness at 320, 360, 390, 430, 600, 768, 1024, 1280, 1440, 1920
- [ ] Accessibility: colour contrast, reduced motion, keyboard navigation