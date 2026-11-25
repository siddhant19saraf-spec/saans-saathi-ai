# Network Resilience Report — SAANS SAATHI AI

**Status:** COMPLETE  
**Date:** Mon Nov 23 2026  
**Engineer:** Principal Full-Stack / DevOps

## Network conditions tested

| Condition | Status | Details |
|---|---|---|
| Normal broadband | PASS | All 175 E2E tests passed on localhost |
| Simulated slow 4G | NOT TESTED | No network throttling configured |
| Simulated slow 3G | NOT TESTED | No network throttling configured |
| Temporary network disconnection | NOT TESTED | No disconnection testing performed |
| API timeout | PARTIAL | Copilot handles timeouts via try/catch |
| Backend unavailable | PARTIAL | DataState shows unavailable state |

Tests were run against localhost (no network latency). Slow network and disconnection scenarios were not simulated.

## Frontend network resilience

### API client (`src/lib/api/client.ts`)

Typed fetch client with:
- Base URL from `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000`)
- Proper `Content-Type: application/json` headers
- Signal-based abort support for cleanup on unmount

### Resource hook (`src/features/api/resource.ts`)

`useApiResource` manages loading/error/success states:
- AbortController for request cancellation on unmount/remount
- Retry callback for idempotent GET requests
- `DataState` component renders appropriate UI for each state

### Data fetching hooks

| Hook | File | Retry | Abort |
|---|---|---|---|
| `useAirCurrent` | `src/features/air-quality/api.ts` | ✅ | ✅ |
| `useAirForecast` | `src/features/air-quality/api.ts` | ✅ | ✅ |
| `useAirHistory` | `src/features/air-quality/api.ts` | ✅ | ✅ |
| `compareEcoRoute` | `src/features/eco-route/api.ts` | ✅ (via signal) | ✅ |
| `fetchFactors` | `src/features/impact/api.ts` | ✅ | ✅ |
| `postCopilotChat` | `src/features/copilot/api.ts` | ❌ (unsafe write) | ✅ |

### Copilot timeout handling

`src/components/copilot/copilot-view.tsx`:
- `try/catch` around `postCopilotChat`
- `classifyApiFailure(error)` categorizes the failure
- Shows user-friendly message ("The Copilot request failed")
- Turn status set to `"error"` with failure details
- No silent failure, no fake answer

### Offline behavior

- No service worker registered
- No offline cache
- No offline functionality claimed
- If backend is unavailable, `DataState` shows unavailable state with message
- localStorage-based features (EcoRoute preferences, Impact log, SmartRoutine, IndoorShield) work offline
- Family profile and recommendation history require backend (server-side session)

### Failed request handling

- `requestfailed` event captured in E2E tests (aborted requests filtered out)
- API failures (>=400) captured and reported
- No unhandled promise rejections

---

## Backend network resilience

### Health endpoints

| Endpoint | Purpose | Status when deps unavailable |
|---|---|---|
| `/healthz` | Liveness | 200 (server running) |
| `/readyz` | Readiness | 503 if deps unreachable |
| `/api/v1/health` | Detailed health | Reports dependency status |

### Provider timeout handling

- Open-Meteo adapter: request timeout configured
- OpenAQ adapter: request timeout configured
- CPCB adapter: reports unavailable (endpoint not verified)
- Provider health: `/api/v1/air-quality/providers/health`

### Database connection failure

- `DATABASE_URL` optional in dev
- Required in production (`APP_ENV=production`)
- Health endpoint reports database status
- Graceful degradation — API endpoints that don't need DB still work

### External provider failure isolation

- Each provider (Open-Meteo, OpenAQ, CPCB) is independent
- One provider failure doesn't affect others
- `/api/v1/air-quality/providers/health` reports per-provider status
- Air quality response includes `source_type` and provenance

---

## API communication verification

Real API calls verified working:

| Endpoint | Method | Status | Data |
|---|---|---|---|
| `/api/v1/air-quality/current?lat=28.61&lon=77.21` | GET | 200 | `cpcb_aqi` value 264 ("poor") |
| `/api/v1/ecoroute/providers/health` | GET | 200 | Provider health status |
| `/api/v1/health` | GET | 200 | Health status |
| `/api/v1/meta` | GET | 200 | API metadata |
| `/healthz` | GET | 200 | Liveness |
| `/readyz` | GET | 200 | Readiness |

CORS:
- `ALLOWED_ORIGINS` configurable (explicit allowlist, no wildcards)
- Default: `frontend_url` (`http://localhost:3000`)
- Production: set via `render.yaml` env vars

---

## Graceful degradation summary

| Scenario | Frontend behavior | Backend behavior |
|---|---|---|
| Backend down | DataState shows "service not connected" | N/A |
| Slow network | Skeletons show during loading | Requests complete eventually |
| Provider unavailable | 503 problem document, no fabricated data | Provider marked unhealthy |
| DB unavailable | Endpoints needing DB return 503 | Health endpoint reports unhealthy |
| CORS misconfigured | Browser blocks request (visible in console) | ACAO header absent |
| API timeout | Copilot shows error message | Request times out cleanly |

---

## What was NOT tested

1. **Slow 4G/3G simulation** — No network throttling tool configured
2. **Temporary disconnection** — No disconnection testing
3. **Offline mode** — No service worker, no offline cache
4. **DNS failure** — Not tested
5. **SSL/TLS failure** — Not tested (HTTP only in dev)

---

## Conclusion

Network resilience: **CONDITIONALLY PASS**. The application handles backend unavailability, API errors, and provider failures gracefully with user-friendly messages. However, slow network (4G/3G simulation) and temporary disconnection scenarios were not tested due to lack of network throttling tooling. No offline functionality is claimed. Production deployment should include network resilience testing with throttled connections.
