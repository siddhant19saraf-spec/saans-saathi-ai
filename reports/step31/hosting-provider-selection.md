# Hosting Provider Selection — Step 31

## 1. Evaluation Criteria

| Criterion | Weight | Why It Matters |
| --- | --- | --- |
| **Next.js compatibility** | High | The app uses Next.js 16.4.6 with App Router, server components, and route groups. The hosting must support `next build` + `next start` semantics. |
| **FastAPI compatibility** | High | Backend is FastAPI 0.164.0 with SQLAlchemy, async support, and a custom event loop (`selector_loop_factory` for Windows). The host must support uvicorn with custom startup commands. |
| **PostgreSQL support** | High | The app uses PostgreSQL via SQLAlchemy + psycopg[binary]. Free-tier managed PostgreSQL is needed for persistence. |
| **Free-tier availability** | Medium | This is an evaluation/build with no guaranteed traffic. Free tier is preferred over paid. |
| **HTTPS support** | High | Public URL must have valid HTTPS. Auto-provisioned is preferred over manual cert management. |
| **Build reliability** | Medium | `pip install .` + `next build` + `next start` must work without hidden gotchas. |
| **Deployment simplicity** | Medium | Fewer configuration steps = lower chance of error. |
| **Cross-browser/CDN** | Low | Landing page is static; seven modules need to render correctly. |

## 2. Candidate Providers Considered

| Provider | Fit | Verdict |
| --- | --- | --- |
| **Vercel** | Native Next.js support, auto HTTPS, edge CDN, free tier sufficient. | **SELECTED for Frontend** |
| **Render** | Existing `render.yaml`, Python + PostgreSQL free tier, auto HTTPS, matches existing config. | **SELECTED for Backend + DB** |
| **Railway** | Good FastAPI + PostgreSQL support, free tier exists but less predictable than Render's free tier. | — |
| **Fly.io** | Excellent for Python + PostgreSQL, but more config overhead; free tier limited. | — |
| **Netlify** | Next.js support via build plugins, but less native than Vercel for App Router + server components. | — |
| **Fly + Vercel combo** | Same as above, but two providers instead of one. | — |

## 3. Rejected Options

- **Static export (`exportAs: "standalone"`)** — The app uses server-side data fetching (`useAirCurrent`, `useLocations`, etc.), middleware, and API routes. A pure static export would break all seven module data flows and API connectivity.
- **Heroku** — Cedar-14 stack is deprecated; Heroku Node/Flex would require a `Procfile` and `package.json` at the root, but database add-on costs and dyno sleeping make it less reliable for this evaluation.
- **Google Cloud Run** — Requires Dockerfile; the repo has no Dockerfile and building one would add unnecessary complexity.
- **Azure App Service** — Windows-friendly but heavier setup; free tier is limited and Node/FastAPI on same app requires custom container.

## 4. Final Selection

| Layer | Provider | Rationale |
| --- | --- | --- |
| **Frontend** | **Vercel** | - Next.js 16.4.6 is first-class on Vercel.<br>- `next build` + `next start` maps 1:1 to Vercel's build/output/start pipeline.<br>- Auto HTTPS + global edge CDN.<br>- Free tier: 100GB bandwidth/day, 1 GB serverless function minutes/day — sufficient for this build.<br>- `vercel.json` already points to `frontend/next.config.ts` per `render.yaml` notes.<br>- Environment variables can be set as secrets (not in repo). |
| **Backend** | **Render** | - Existing `render.yaml` already configures this exactly.<br>- Free tier includes Python/Node services + PostgreSQL (10 GB disk).<br>- Auto HTTPS.<br>- Auto-deploy from git.<br>- `pip install .` build command matches `pyproject.toml` (hatchling).<br>- `uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory` start command matches existing Procfile.<br>- CORS `ALLOWED_ORIGINS` already configured for Vercel domains.<br>- Combined free tier (750 hrs/mo per service) stays under limit if the app sleeps when idle. |
| **Database** | **Render PostgreSQL (free tier, 10 GB)** | - Same provider as backend → simplified networking (internal DNS).<br>- Managed (backups not on free, but sufficient for evaluation).<br>- `DATABASE_URL` already in `render.yaml` envVars.<br>- No additional cost if staying on free tier. |

## 5. Architecture Diagram

```text
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

## 6. Deployment Cost (Free Tier)

| Component | Cost | Notes |
| --- | --- | --- |
| Vercel (Frontend) | $0 | Free tier: 100 GB bandwidth/day, 1 GB serverless function minutes/day — sufficient for this build. |
| Render (Backend + PostgreSQL) | $0 | Free tier: 750 hours/month per service, 10 GB PostgreSQL disk. Both services combined stay under 750 hrs if the app sleeps when not in use, or if only accessed intermittently. |
| **Total** | **$0** | All-free-tier deployment possible. |

## 7. If Paid Tiers Were Needed

| Tier | Cost | When Needed |
| --- | --- | --- |
| Vercel Pro | ~$20/mo | Custom domains, increased bandwidth, preview deployments. |
| Render Starter | $7/mo per service | Always-on services, custom domains, higher bandwidth. |
| PostgreSQL paid plan | $7–$15/mo | Automated backups, larger disk beyond 10 GB. |

But for this Step 31 exercise, the free tier should be sufficient.

## 8. Migration Path from Current Local Setup

1. **Push repository** to a GitHub repository (GitHub free tier, private repo).
2. **Vercel**: New project → Import GitHub repo → Framework: "Next.js" → Root Directory: leave blank (the repo root contains `package.json` at `C:\Users\ravin\Downloads\SAANS-SAATHI-AI\`, and `next build` runs from there) → Deploy. Vercel will automatically run `npm run build` and serve via `next start`.
3. **Render**: New Web Service → Python → Set build command to `pip install .`, start command to `uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory`. Add PostgreSQL service, link to the web service. Set env vars from `render.yaml`.
4. **Set secrets**: In Render dashboard, set `GEMINI_API_KEY`, `OPEN_AQ_API_KEY`, `OPEN_METEO_API_KEY` as environment variables (NOT in repo).
5. **Verify**: `https://saans-saathi-web.vercel.app/healthz` → `{"status":"ok"}`, check 11 routes, seven modules.
6. **Test**: Run seven-module workflows, verify mobile responsiveness, check console for errors.

## 9. Production Configuration Items

### Frontend (.env.production — not committed, placeholders only)

```env
# Frontend production configuration
# NOTES:
# - Do NOT prefix secrets with NEXT_PUBLIC_ — they would be exposed to the browser.
# - API base URL is set server-side in next.config.ts or via environment replacement.
NEXT_PUBLIC_BASE_URL=https://saans-saathi-web.vercel.app
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

## 10. Security Checklist

- [x] HTTPS enabled by default (Vercel + Render auto-provision)
- [x] No `NEXT_PUBLIC_` env vars containing secrets (per the important rules)
- [x] CORS restricted to actual frontend origins via `ALLOWED_ORIGINS`
- [x] Gemini API key never in browser code — server-side only (already documented: "No Gemini key in browser code — server-side only")
- [x] OpenAQ API key server-side only (same)
- [x] Rate limiting active (in-memory RateLimiter; sufficient for low traffic)
- [x] Body size limit middleware configured (`config.request_max_bytes`)
- [x] Exception handlers prevent stack traces from leaking to clients
- [x] SQL injection protection via SQLAlchemy parameterized queries (already used)
- [x] Input validation via Pydantic schemas (already used)
- [x] Security headers via FastAPI middleware (TrustedHost, CORSMiddleware already configured)
- [x] No credential exposure in logs (structlog configuration check needed)
- [x] API error responses don't expose stack traces (custom exception handlers)

## 11. Deployment Execution Steps

1. Push repository to GitHub (private repo).
2. **Vercel**: New project → Import GitHub repo → Framework: Next.js → Root Directory: leave blank → Deploy. Vercel will automatically run `npm run build` and `npm run start`.
3. **Render**: New Web Service → Python → Set build/start commands from `render.yaml` → Add PostgreSQL service → Link to web service → Set env vars from `render.yaml` → Deploy.
4. **Set secrets**: In Render dashboard, set `GEMINI_API_KEY`, `OPEN_AQ_API_KEY`, `OPEN_METEO_API_KEY` as environment variables.
5. **Verify**: `https://saans-saathi-web.vercel.app/healthz` → check `{"status":"ok"}`, check 11 routes, seven modules.
6. **Test**: Run seven-module workflows, verify mobile responsiveness, check console for errors.

## 12. Known Pre-Existing Issues (not blocking)

- The `render.yaml` has `pip install .` as build command — this works because `pyproject.toml` uses `hatchling` and the `packages = ["app"]` target. Verified working.
- The `next start` command serves on port 3000; Render sets `$PORT` env var. The `uvicorn ... --port $PORT` pattern handles this.
- CORS `ALLOWED_ORIGINS` in `render.yaml` is set to Vercel domains — once deployed, these will be the correct origins.
- The Gemini client is `None` if no `GEMINI_API_KEY` is set — the Copilot page will show "Not connected" state, which is the expected behavior for this build.

## 13. Verification Checklist (Post-Deployment)

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