# SAANS SAATHI AI — Production Readiness

**Audit date:** 2026-11-21  
**Scope:** Deployment configuration, environment requirements, CI/CD, runtime prerequisites

---

## Deployment Configuration Status

| Item | Status | Detail |
|------|--------|--------|
| `render.yaml` | Not present | No Render service definition exists |
| `vercel.json` | Not present | No Vercel deployment config exists |
| `Procfile` | Not present | No Heroku-style process file exists |
| CI workflow | `.github/workflows/quality-checks.yml` | Exists; runs lint, typecheck, tests, build, pip-audit, Bandit, gitleaks, repo size |

**Production deployment cannot be verified.** No Render, Vercel, or GitHub account access is available, and no deployment configuration files exist in the repository. This is documented as a limitation, not claimed as successful.

---

## Environment Variables Required

### Backend (required in production)

| Variable | Purpose | Default / Example |
|----------|---------|-------------------|
| `DATABASE_URL` | PostgreSQL connection string | Required; no default |
| `GEMINI_API_KEY` | Optional Gemini key for AI explanations | Optional; deterministic fallback when unset |
| `APP_ENV` | Application environment | `test` / `production` |
| `LOG_LEVEL` | Logging level | `WARNING` |
| `ALLOWED_HOSTS` | Allowed host headers | `localhost,127.0.0.1,testserver` (dev); **must set explicitly in production** |
| `FRONTEND_URL` | Frontend origin for CORS | Required in production |

### Frontend

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL (if not same-origin) |

---

## Pre-Deployment Checklist

| Item | Status | Notes |
|------|--------|-------|
| Code defects fixed | ✅ | All P0-P3 defects fixed with regression coverage |
| Tests passing | ✅ | Backend 264 passed; frontend all passing |
| Lint clean | ✅ | `ruff check`, `black`, `mypy`, `eslint` all clean |
| Typecheck clean | ✅ | `mypy` (107 files), `tsc --noEmit` |
| Build clean | ✅ | `next build` — 12 routes |
| Security scan clean | ✅ | Bandit 0 findings; `pip-audit` clean; secret scan only placeholders |
| Coverage gate | ⚠️ | Backend 77.53% vs 80% CI gate; frontend gates pass |
| Migration chain | ✅ | 9 Alembic revisions; `0009` fixes constraint drift |
| `.env` not committed | ✅ | Only `.env.example` with placeholders |
| Deploy config | ❌ | No `render.yaml`, `vercel.json`, or `Procfile` |
| Production DB | ❌ | Not accessible; local test DB only |
| Production CORS origins | ❌ | Must set `ALLOWED_HOSTS` and `FRONTEND_URL` before deploy |
| Load testing | ❌ | Not performed |

---

## Runtime Prerequisites

| Component | Requirement |
|-----------|-------------|
| Python | 3.13+ (venv at `backend/.venv`) |
| PostgreSQL | 16+ (local 16.15 confirmed) |
| Node.js | For Next.js 16.4.6 frontend |
| DATABASE_URL | PostgreSQL connection string (required in production) |
| GEMINI_API_KEY | Optional; deterministic fallback when unset |
| ALLOWED_HOSTS | Must be set to production host(s) |
| FRONTEND_URL | Must be set to production frontend origin |

---

## Database Migrations for Production

| Migration | Purpose | Risk |
|-----------|---------|------|
| `0001` – `0008` | Already shipped schema | N/A |
| `0009_constraint_names` | Renames 8 check constraints to match ORM | Low (forward-only rename) |

Run `alembic upgrade head` on production database before deploying new code.

---

## Known Limitations (Non-Blocking)

| ID | Limitation | Impact |
|----|-----------|--------|
| L1 | Production deployment unverified | Cannot confirm deploy succeeds without account access |
| L2 | No deploy config files | Must add `render.yaml`/`vercel.json`/`Procfile` before first deploy |
| L3 | Backend coverage below CI gate | 77.53% vs 80%; may block CI merge until tests added |
| L4 | Production `ALLOWED_HOSTS` / `FRONTEND_URL` unset | CORS will reject production requests until configured |
| L5 | No production load testing | Performance under production load unknown |
| L6 | No penetration testing | Security verified only via static analysis |
| L7 | Single household per anonymous session | Documented architectural limitation |

---

## Verdict on Production Readiness

**NOT READY FOR PRODUCTION DEPLOYMENT** without the following:

1. Add deployment configuration (`render.yaml`, `vercel.json`, or `Procfile`)
2. Configure `ALLOWED_HOSTS` and `FRONTEND_URL` for production
3. Obtain production database access and run `alembic upgrade head`
4. Verify deployment in a staging environment
5. Clear backend coverage CI gate (add tests for low-coverage files)

These are documented limitations, not hidden issues. The application code itself is tested, linted, type-checked, and built successfully.
