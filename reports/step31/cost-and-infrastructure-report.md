# Cost and Infrastructure Report — Step 31

## 1. Infrastructure Overview

| Layer | Provider | Service | Tier | Monthly Cost |
| --- | --- | --- | --- | --- |
| **Frontend** | Vercel | Next.js 16.4.6 hosting + edge CDN | Free | $0 |
| **Backend** | Render | FastAPI 0.164.0 (Python) + Python service | Free | $0 |
| **Database** | Render | PostgreSQL (managed) | Free (10 GB disk) | $0 |
| **Version Control** | GitHub | Private repository + Git actions | Free | $0 |
| **DNS** | Vercel (automatic) | `saans-saathi-web.vercel.app` CNAME | Free | $0 |
| **Monitoring** | UptimeRobot (free) | Uptime pings (frontend + backend) | Free | $0 |
| **Analytics** | Vercel Analytics | Page views, visits, error rates | Free (limited) | $0 |

## 2. Cost Breakdown (Free Tier)

| Component | Free Tier Limits | Expected Usage (this build) | Cost |
| --- | --- | --- | --- |
| **Vercel (Frontend)** | - 100 GB bandwidth per day<br>- 1 GB serverless function minutes per day<br>- Unlimited projects<br>- Automatic HTTPS<br>- Edge CDN included | - Landing page: ~10 KB per visit<br>- 7 modules: ~50–100 KB per visit<br>- Estimated: < 1 GB/mo bandwidth<br>- < 1 GB function minutes/mo | $0 |
| **Render (Backend + PostgreSQL)** | - 750 hours per month per service<br>- 10 GB PostgreSQL disk (free)<br>- Automatic HTTPS<br>- Deploy from Git<br>- Free-tier PostgreSQL: no automated backups, no SSL enforcement<br>- Services auto-sleep after inactivity (saves hours) | - Backend: ~700 hrs/mo (always-on) or ~100 hrs/mo (if it sleeps when idle)<br>- PostgreSQL: < 10 GB disk (evaluation data only)<br>- If always-on: 750 hrs/mo exactly; if sleep-enabled: < 750 hrs/mo | $0 (always-on) / $0 (sleep-enabled) |
| **GitHub** | - Unlimited private repos<br>- 2,000 min/mo CI/CD (free)<br>- Actions workflows | - No CI/CD workflows added (manual deployment)<br>- Repo size < 100 MB | $0 |
| **UptimeRobot (free)** | - 50 monitors<br>- 5 min check interval<br>- Email/Slack alerts | - 2 monitors (frontend + backend)<br>- Well within 50-limit | $0 |
| **Vercel Analytics** | - Built-in; limited metrics<br>- No additional cost | - Basic page view counts<br>- Suffices for evaluation | $0 |

**Total Monthly Cost**: **$0** (all-free-tier).

## 3. If Paid Tiers Were Upgraded

| Tier | Component | Cost | When Needed |
| --- | --- | --- | --- |
| **Vercel Pro** | Frontend | ~$20/mo | Custom domain, increased bandwidth (>100 GB/day), preview deployments, team collaboration. |
| **Vercel Enterprise** | Frontend | ~$200+/mo | Advanced analytics, governance, priority support, global regions. |
| **Render Starter** | Backend + DB | $7/mo per service | Always-on services (no sleep), custom domains, higher bandwidth, backups (PostgreSQL). |
| **Render PostgreSQL Paid** | Database | $7–$15/mo | Automated backups, larger disk (>10 GB), point-in-time recovery. |
| **UptimeRobot Premium** | Monitoring | $5–$10/mo | 5-min interval already on free; Premium adds 1-min interval, more monitors, SMS alerts. |

**But for this Step 31 exercise, the free tier is sufficient**.

## 4. Infrastructure Diagram

```text
+----------------------+       HTTPS       +----------------------+
|  Vercel (Frontend)   |  <-------------> |  Render (Backend)    |
|  - Next.js 16.4.6    |  HTTPS + CDN    |  - FastAPI 0.164.0  |
|  - / route           |-----------------|  - SQLAlchemy ORM   |
|  - /dashboard etc.   |               |  - Alembic migrations|
|  - Static assets    |               |  - psycopg + PostgreSQL|
|  - API routes       |               |  - Rate limiter      |
+----------------------+               +----------------------+
          |                                 |
          |   +---------------------------+   |
          +-->|  PostgreSQL (free, 10 GB) |<--+
              |  10 GB disk, managed     |
              +---------------------------+
```

## 5. Dependencies (Production)

| Dependency | Version | Source | License |
| --- | --- | --- | --- |
| **fastapi** | 0.164.0 | `pyproject.toml` (hatchling) | MIT |
| **uvicorn** | 0.54.0 | `pyproject.toml` | BSD-3-Clause |
| **sqlalchemy** | 2.1.9 | `pyproject.toml` | MIT |
| **psycopg[binary]** | 3.3.9 | `pyproject.toml` | BSD-3-Clause |
| **alembic** | 1.20.1 | `pyproject.toml` | MIT |
| **next** | 16.4.6 | `frontend/package.json` | MIT |
| **react** | 19.3.1 | `frontend/package.json` | MIT |
| **tailwindcss** | v4 | `frontend/globals.css` | MIT |
| **structlog** | 26.1.0 | `backend/pyproject.toml` | MIT |
| **bandit** | 1.9.4 | dev dependency | GPL-2.0+ |

All dependencies are open‑source and MIT/BSD-compatible; no copyleft issues.

## 6. Deployment Artifacts

| Artifact | Location | Description |
| --- | --- | --- |
| **`backend/render.yaml`** | `C:\Users\ravin\Downloads\SAANS-SAATHI-AI\backend\render.yaml` | Combined backend + frontend + PostgreSQL config (single `services:` list). |
| **`frontend/package.json`** | `C:\Users\ravin\Downloads\SAANS-SAATHI-AI\frontend\package.json` | Scripts: `dev`, `build`, `start`, `lint`, `test`, `check`. |
| **`backend/procfile`** | `C:\Users\ravin\Downloads\SAANS-SAATHI-AI\backend\Procfile` | `uvicorn app.main:app --port $PORT --loop app.core.loop:selector_loop_factory`. |
| **`backend/.env.example`** | Not explicitly created; see `backend-production-configuration.md` for placeholders. | — |
| **`frontend/next.config.ts`** | Not yet created (would add for production headers). | — |
| **`reports/step31/`** | `C:\Users\ravin\Downloads\SAANS-SAATHI-AI\reports\step31/` | 13 required reports (this list + FINAL-STEP31-REPORT.md). |

## 7. Summary

| Item | Value |
| --- | --- |
| **Total monthly cost** | $0 (all-free-tier) |
| **Frontend provider** | Vercel (free tier sufficient) |
| **Backend provider** | Render (free tier sufficient) |
| **Database provider** | Render PostgreSQL free tier (10 GB) |
| **Version control** | GitHub (free tier) |
| **Monitoring** | UptimeRobot free + Render dashboard built-in |
| **Infrastructure complexity** | Low (two providers, one database; all managed) |
| **Scalability path** | Vercel Pro + Render Starter + PostgreSQL paid plan (if traffic grows) |
| **HTTPS** | Auto‑provisioned by both Vercel and Render |
| **Domain** | `saans-saathi-web.vercel.app` (Vercel default); custom domain optional. |

## 8. Infrastructure Checklist (Pre‑Deployment)

- [ ] GitHub repo created (private, empty or with existing code).
- [ ] Vercel account connected to GitHub repo.
- [ ] Render account created; Python + PostgreSQL services provisioned.
- [ ] `render.yaml` config reviewed (build/start commands, env vars).
- [ ] Secrets set in Vercel dashboard (`NEXT_PUBLIC_BASE_URL`).
- [ ] Secrets set in Render dashboard (`GEMINI_API_KEY`, `OPEN_AQ_API_KEY`, `ALLOWED_ORIGINS`, `FRONTEND_URL`, `DATABASE_URL`).
- [ ] No credentials in repo (`.gitignore` covers `.env*`, `*.key`, etc.).
- [ ] Deployment order verified: PostgreSQL first, then backend, then frontend.
- [ ] Rollback plan documented (revert to previous Git commit on both platforms).
- [ ] Monitoring (UptimeRobot) added: 2 monitors (frontend + backend health).

## 9. Post-Deployment Cost Verification

After deployment, the following will be verified:

- [ ] Vercel dashboard: bandwidth usage < 100 GB/day; function minutes < 1 GB/day.
- [ ] Render dashboard: service hours < 750 hrs/mo (or sleep-enabled < 750 hrs).
- [ ] Render PostgreSQL disk usage < 10 GB.
- [ ] No unexpected charges from either provider.
- [ ] Cost remains $0/mo for the duration of the evaluation build.

## 10. Infrastructure Conclusion

The Step 31 deployment uses a minimal two‑provider infrastructure (Vercel + Render) with all components on free tiers. The total cost is $0/month, which satisfies the "do not introduce paid infrastructure without disclosing costs" rule. The architecture is simple, reliable, and sufficient for an evaluation‑grade build with expected low traffic. If the product moves to production with higher traffic, the upgrade path is well‑defined (Vercel Pro → Enterprise, Render Starter → PostgreSQL paid).