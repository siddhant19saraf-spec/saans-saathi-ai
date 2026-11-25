# Monitoring and Reliability — Step 31

## 1. Frontend Availability Monitoring

| Metric | Method | Frequency | Expected | Alert |
| --- | --- | --- | --- | --- |
| **Uptime** | Vercel dashboard "Analytics" → Uptime | Continuous | 99%+ (free tier) | None (Vercel handles automatic retries). |
| **Status code** | `curl -o /dev/null -w "%{http_code}" https://saans-saathi-web.vercel.app/` | Every 5 min (cron/uptimeRobot) | 200 | If non-200, trigger PagerDuty/email. |
| **Response time** | Browser `performance.now()` on page load | Every 5 min | < 2 s (cold start), < 500 ms (warm) | If degraded, check Vercel logs. |
| **Console errors** | Vercel frontend logs | Every deploy + daily | 0 critical (only Next.js runtime messages) | If spike, investigate. |

### Monitoring Tools

- **Vercel Analytics**: Built-in; shows visits, page views, error rates.
- **UptimeRobot (free tier)**: Ping `https://saans-saathi-web.vercel.app/` every 5 min; alerts via email/Slack.
- **Google Search Console**: Monitor indexing and any crawl errors (not critical for this build).

## 2. Backend Health Monitoring

| Metric | Method | Frequency | Expected | Alert |
| --- | --- | --- | --- | --- |
| **`/healthz` liveness** | `GET https://<render-service>.onrender.com/healthz` | Every 1 min (cron) | `{"status":"ok"}` + 200 | If non-200 or different body, restart service. |
| **Uptime** | Render dashboard "Service uptime" | Continuous | 99%+ (free tier: 750 hrs/mo) | None (Render auto-restarts on crash). |
| **Response time** | `time curl -s -o /dev/null -w "%{time_total}" https://<render-service>.onrender.com/healthz` | Every 5 min | < 2 s | If degraded, check PostgreSQL connectivity. |
| **PostgreSQL connectivity** | `psql "postgres+psycopg://..." -c "SELECT 1;"` | Every 5 min | `QUERY: 1` (row) | If fails, check Render PostgreSQL status. |
| **CORS header** | Verify `Access-Control-Allow-Origin` on API calls | Every deploy | `https://saans-saathi-web.vercel.app` | If missing, check `ALLOWED_ORIGINS` secret. |
| **Rate limiter status** | Custom endpoint (if added) or logs | On error only | No 429 responses for legitimate traffic | If 429, increase TTL or check traffic spike. |

### Monitoring Tools

- **Render Dashboard**: Built-in service metrics (CPU, memory, request rate, error rate).
- **Render Health Checks**: Auto-pings `/healthz`; if 3 consecutive failures, service is restarted.
- **UptimeRobot**: Also pings the Render `.onrender.com` URL (if it responds; may sleep on free tier).
- **Structlog JSON logs**: Sent to Render logs; can be tailed via the dashboard.

## 3. API Response Status Monitoring

| Endpoint | Expected Response | Expected Status | Monitoring Method |
| --- | --- | --- | --- |
| `GET /healthz` | `{"status":"ok"}` | 200 | UptimeRobot + custom cron. |
| `GET /api/v1/air-quality/current?lat=28.61&lon=77.21` | 200 + AQI data + provenance | 200 | Fetch from frontend; verify CORS header + JSON contains `aqi`, `category`, `pm25`, etc. |
| `GET /api/v1/locations` | 200 + locations list | 200 | If deployed with PostgreSQL data; otherwise returns empty `[]`. |
| `GET /api/v1/settings` | 200 + settings object | 200 | Checks `ALLOWED_ORIGINS` + auth (if enabled). |

**Alerting**: If any endpoint returns non-200 or malformed JSON, trigger an incident via email/Slack.

## 4. Response Latency Monitoring

| Metric | Threshold | Alert Condition |
| --- | --- | --- |
| **Frontend page load** (Time to First Byte) | < 2 s (warm), < 5 s (cold Vercel start) | If > 5 s for 3 consecutive checks, investigate Vercel plan/logs. |
| **Backend `/healthz`** | < 1 s | If > 2 s, check PostgreSQL connectivity + Render service metrics. |
| **Backend API `/api/v1/air-quality/current`** | < 3 s (including external API calls) | If > 5 s, check external API (CPCB/OpenAQ) latency + `AI_REQUEST_TIMEOUT_SECONDS=30`. |
| **Recharts chart resize** | < 500 ms (client-side) | If > 1 s, check image/asset loading. |

**Tools**: 
- Web Vitals extension (Chrome) for frontend.
- `curl -w "%{time_total}" -o /dev/null -s` for backend.
- Render dashboard for overall service latency.

## 5. Deployment Failure Monitoring

| Failure Mode | Detection | Auto-Recovery |
| --- | --- | --- |
| **Vercel build failure** | Vercel dashboard → "Build failed"; commit status `failure` on GitHub. | Redeploy previous commit; fix build error in code. |
| **Render build failure** | Render dashboard → "Build failed"; service stays on previous version. | Fix `pip install .` or `startCommand`; redeploy. |
| **PostgreSQL connection failure** | Render PostgreSQL status page → "Offline"; `/healthz` returns 500/timeout. | Render auto-restarts PostgreSQL; or manual restart via dashboard. |
| **Render service crash** | Service logs → `uvicorn` exit code non-zero; UptimeRobot alert (500 or timeout). | Render auto-restarts the web service (free tier: up to 3 restarts per day, or continuous on paid). |
| **External API timeout** (CPCB/OpenAQ) | `httpx` timeout of 30 s; logs show `RequestException`. | Graceful fallback: Copilot shows "Not connected"; AQI shows `—` (unavailable). |
| **Missing environment variable** | Render logs → `KeyError` or `ValidationError` at startup. | Add missing secret to Render dashboard; redeploy. |

## 6. Graceful Failure Handling

### Frontend (Next.js + React 19)

- **404 pages**: Next.js automatically serves `/404` for missing routes; the UI shows a friendly message.
- **API errors**: `fetch()` errors are caught via `react-hook-form`/`zod` error handling; the UI shows "Failed to load data — please retry."
- **Reduced motion**: `[data-reduce-motion="true"]` collapses all transitions to `0.01ms` (configured in `globals.css`).
- **Error boundaries**: Not explicitly defined, but Next.js route-level error handling catches unhandled errors.

### Backend (FastAPI + Structlog)

- **Exception handlers**: `register_exception_handlers` returns `JSONResponse(status_code=500, content={"error":"internal server error"})` — no stack traces.
- **HTTP timeout**: `httpx` client has `timeout=AI_REQUEST_TIMEOUT_SECONDS=30`; on timeout, the endpoint returns `{"error":"external api timeout"}` (if implemented) or the request is retried.
- **Database unavailable**: SQLAlchemy `OperationalError` is caught by the exception handler; returns `{"error":"database unavailable"}`.
- **Rate limiting**: In-memory RateLimiter returns `429 Too Many Requests` with `Retry-After` header when `max_requests` is exceeded.

## 7. Monitoring Configuration (Production-Ready)

### Frontend (`vercel.json` — already present)

```json
{
  "framework": "nextjs",
  "functions": {
    "api/**": {
      "maxDuration": 30
    }
  }
}
```

- **`maxDuration: 30`**: Limits serverless function execution to 30 seconds (matches `AI_REQUEST_TIMEOUT_SECONDS`).
- **Vercel automatically** adds security headers, analytics, and fallback protection.

### Backend (`render.yaml` — already present)

- **Health checks**: Render auto-pings `/healthz`; 3 consecutive failures → service restart.
- **Logs**: Structured (JSON or plain) via `structlog`; available in Render dashboard.
- **Environment variable validation**: At startup, missing `DATABASE_URL` or `ALLOWED_ORIGINS` would cause a startup error, rendering the service offline until fixed.

### Alerting (Recommended, Free Tier)

| Tool | Cost | What It Monitors |
| --- | --- | --- |
| **UptimeRobot (free)** | $0 | Frontend (`https://saans-saathi-web.vercel.app/`) every 5 min; backend (`https://<service>.onrender.com/healthz`) every 5 min. |
| **Render Dashboard** | $0 (built-in) | Service uptime, CPU/memory, request rate, error rate, PostgreSQL status. |
| **Vercel Analytics** | $0 (free tier) | Visits, page views, error rates, performance. |
| **Google Search Console** | $0 | Indexing status, crawl errors (optional). |

**No paid monitoring services are required** for this evaluation build.

## 7. Reliability Goals (Step 31 Acceptance)

| Goal | Target | Status (Local) |
| --- | --- | --- |
| **Frontend availability** | 99%+ uptime | ✅ `next start` runs locally; Vercel free tier expected. |
| **Backend availability** | 99%+ uptime | ✅ `uvicorn` runs locally; Render free tier expected. |
| **API connectivity** | 100% of requests succeed when data is available | ✅ All 11 routes + `/healthz` verified locally. |
| **Graceful degradation** | No fake data; honest empty states (`—`) | ✅ Verified in Step 29/30; no fabricated AQI/sensor data. |
| **Error leakage** | No stack traces to clients | ✅ Custom exception handlers registered. |
| **Rate limiting** | No 429 for legitimate traffic | ✅ In-memory RateLimiter configured; sufficient for low traffic. |

## 8. Monitoring Checklist (Post-Deployment)

- [ ] UptimeRobot (or similar) pinging frontend + backend every 5 min.
- [ ] Render health check auto-ping `/healthz` (built-in).
- [ ] Vercel Analytics loaded; no unexpected error spikes.
- [ ] Structured logs (structlog) available in Render dashboard.
- [ ] CORS header verified on every API call.
- [ ] Rate limiter not blocking legitimate traffic.
- [ ] No `NEXT_PUBLIC_` secrets exposed in browser dev tools.
- [ ] Exception handlers tested (force an error → verify generic response).
- [ ] PostgreSQL connection monitored (Render dashboard).
- [ ] Response latency within thresholds (see section 5).
- [ ] Backup plan documented (Render free‑tier manual export if needed).