# Security Hardening Report

## Confirmed Fixes

### P0: DATABASE_URL Scheme Validation (CONFIG-001)
- **Issue:** `render.yaml` declared `DATABASE_URL: postgres+psycopg://postgres:postgres@db:5432/saans_prod`, but the FastAPI `Settings` validator rejects `postgres+psycopg` scheme, requiring `postgresql+psycopg`. A deployed instance would fail at startup.
- **Fix:** Changed `DATABASE_URL` to `postgresql+psycopg://postgres:postgres@db:5432/saans_prod` in `backend/render.yaml` and `README.md`.
- **Verification:** Backend pytest suite runs successfully with `$env:TEST_DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/saans_test'`.

### CORS Hardening (Pre-existing, verified)
- **Allowlist:** `ALLOWED_ORIGINS` = `http://localhost:3000,http://localhost:3001` locally; wildcards rejected by config validation.
- **Headers:** `x-content-type-options: nosniff`, `x-frame-options: DENY`, `referrer-policy: no-referrer` present on all responses including `/healthz`.
- **Origin checking:** CORS middleware validates origins against the allowlist; missing origin defaults to restrictive behavior.

### HTTP Security Headers (Verified)
| Header | Value | Presence |
|--------|-------|----------|
| `X-Content-Type-Options` | `nosniff` | ✅ All responses |
| `X-Frame-Options` | `DENY` | ✅ All responses |
| `Referrer-Policy` | `no-referrer` | ✅ All responses |
| `Content-Security-Policy` | Not set (beyond current scope) | ⚠️ |

### Backend Health Endpoint
- `GET http://localhost:8000/healthz` → `{"status":"ok"}` with all three security headers present.
- Responds with `200 OK` and JSON body.

## Vulnerability Assessment

### Cross-Site Scripting (XS)
- No user-generated HTML rendered without sanitization in the seven module views.
- All dynamic content flows through Recharts, Radix, or Lucide React components which escape by default.
- No `dangerouslySetInnerHTML` usage found in the codebase.

### Injection Points
- Air quality location search (`fetchLocationSearch`) validates via Zod schema before API call.
- Copilot chat input validated via `copilotAnswerSchema` Zod schema.
- Routine activity form validated via `routineActivityFormSchema` Zod schema.
- Impact activity form validated via `impactActivityFormSchema` Zod schema.
- All form inputs go through Zod refinements for numeric ranges, enum values, and format patterns.

### Rate Limiting
- `app/core/rate_limit.py` implements sliding-window rate limiter per process.
- Unmetered public endpoints protected; AI dependency (Gemini) has dedicated limit.
- Comment in code states: "Proxy deployments must enable `--proxy-headers` so the client address is the real caller, never a spoofable forwarded value."

### Dependency Versions (Current)
| Package | Version | Notes |
|---------|---------|-------|
| FastAPI | 0.164.0 | Latest in 0.164.x series |
| Python | 3.13.14 | >=3.12,<3.14 |
| SQLAlchemy | 2.1.9 | Async support |
| psycopg | 3.3.9 | Async driver |
| Alembic | 1.20.1 | Migration tool |
| structlog | 26.1.0 | Structured logging |
| uvicorn | 0.54.0 | ASGI server |

## Remaining Security Items
- **Content-Security-Policy:** Not yet configured; would require adding `meta http-equiv` or middleware. Out of scope for P0/P1 but noted for future hardening.
- **HTTPS in production:** Currently verified over `http://localhost:3000` and `http://localhost:8000`. Production deployment via Vercel/Render will enforce HTTPS.
- **Secret rotation:** `GEMINI_API_KEY` and other API keys stored in environment; no secrets in source. Vercel/Render dashboard manages secret injection.