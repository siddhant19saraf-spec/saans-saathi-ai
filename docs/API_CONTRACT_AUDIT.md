# SAANS SAATHI AI — API Contract Audit

**Audit date:** 2026-11-21  
**Scope:** Every backend route (`/api/v1/*`) and frontend API client surface audited against its schema contract. All responses use the standard envelope `{ data, meta: { request_id } }`; errors use `{ type, title, status, detail, code, request_id }`.

---

## Backend Routes

### Authentication & Sessions — `/api/v1/sessions`

| Method | Path | Status codes | Contract notes |
|--------|------|-------------|----------------|
| POST | `/api/v1/sessions` | 201, 401, 429 | Creates anonymous session; body `{ consent_version, health_consent }`; returns `{ token, expires_at, profile_id }` |
| POST | `/api/v1/sessions/me/consent` | 200, 401, 429 | Grants health-data consent; body `{ health_consent: true }`; returns consent info |
| DELETE | `/api/v1/sessions/me` | 204, 401 | Deletes session and all associated data |

All session routes require no bearer token (public). Rate-limited per session/IP.

---

### Household — `/api/v1/household`

| Method | Path | Auth | Status codes | Contract notes |
|--------|------|------|-------------|----------------|
| GET | `/api/v1/household` | Bearer | 200, 401, 404 | Returns household with members; 404 if none exists |
| PUT | `/api/v1/household` | Bearer | 200, 401, 409, 429 | Upsert; `HouseholdUpsert` schema; creates preferences on demand |
| POST | `/api/v1/household/members` | Bearer | 201, 403, 404, 409, 429 | Add member; health flags require `health_consent` (403 `CONSENT_REQUIRED`) |
| PATCH | `/api/v1/household/members/{member_id}` | Bearer | 200, 403, 404, 429 | Update member; health flags require consent |
| DELETE | `/api/v1/household/members/{member_id}` | Bearer | 204, 404 | Remove member |
| GET | `/api/v1/household/preferences` | Bearer | 200, 401, 409 | Returns `PreferencesResponse`; 409 if no household |
| PUT | `/api/v1/household/preferences` | Bearer | 200, 401, 409, 429 | Replace preferences; activity windows validated by schema |
| GET | `/api/v1/household/locations` | Bearer | 200, 401, 409 | List saved locations |
| POST | `/api/v1/household/locations` | Bearer | 201, 401, 409, 429 | Save location; label must be unique per household (409 `CONFLICT`) |
| DELETE | `/api/v1/household/locations/{location_id}` | Bearer | 204, 404, 409 | Delete saved location |

---

### Family — `/api/v1/family`

| Method | Path | Auth | Status codes | Contract notes |
|--------|------|------|-------------|----------------|
| POST | `/api/v1/family/profile` | Bearer | 201, 403, 404, 409, 429 | Create family profile; `ProfileInput` schema; health flags require consent |
| GET | `/api/v1/family/profile` | Bearer | 200, 401, 404 | Read profile; 404 = first-run state (not error) |
| PUT | `/api/v1/family/profile` | Bearer | 200, 401, 404, 409, 429 | Replace profile |
| DELETE | `/api/v1/family/profile` | Bearer | 204, 401, 404 | Delete profile and all recommendations |
| GET | `/api/v1/family/preferences` | Bearer | 200, 401, 404, 409 | Read preferences; 404 if none set |
| PUT | `/api/v1/family/preferences` | Bearer | 200, 401, 404, 409, 429 | Replace preferences |
| POST | `/api/v1/family/recommendations/generate` | Bearer | 200, 401, 404, 409, 429 | Generate recommendations via deterministic rules engine + optional Gemini |
| GET | `/api/v1/family/recommendations` | Bearer | 200, 401, 404 | List recommendation history; `limit`/`offset` pagination |
| GET | `/api/v1/family/recommendations/{recommendation_id}` | Bearer | 200, 401, 404 | Read single recommendation |

---

### SmartRoutine — `/api/v1/routines`

| Method | Path | Auth | Status codes | Contract notes |
|--------|------|------|-------------|----------------|
| GET | `/api/v1/routines/activities` | Bearer | 200, 401, 409 | List active activities; `ActivityList` envelope |
| POST | `/api/v1/routines/activities` | Bearer | 201, 401, 409, 422 | Create activity; validates window, venue, member ownership, fixed overlaps, max 20 |
| PUT | `/api/v1/routines/activities/{activity_id}` | Bearer | 200, 401, 404, 409, 422 | Update activity; partial updates re-validated against stored values |
| DELETE | `/api/v1/routines/activities/{activity_id}` | Bearer | 204, 404, 409 | Soft-delete (idempotent) |
| GET | `/api/v1/routines` | Bearer | 200, 401, 404 | Read active routine for date; 404 if none generated |
| GET | `/api/v1/routines/{routine_id}` | Bearer | 200, 401, 404 | Read specific routine version |
| POST | `/api/v1/routines/generate` | Bearer | 200, 401, 404, 409, 422, 429, 503 | Generate deterministic plan; requires household + members + activities + forecast coverage |
| POST | `/api/v1/routines/{routine_id}/replan` | Bearer | 200, 401, 404, 409, 422, 429 | Replan active routine; 409 `ROUTINE_SUPERSEDED` if not active |
| PUT | `/api/v1/routines/{routine_id}/activities/{activity_id}` | Bearer | 200, 401, 404, 409, 422 | Manual change + regenerate; supports `cancel` |
| PATCH | `/api/v1/routines/{routine_id}/items/{block_id}` | Bearer | 200, 401, 404 | Mark item done/skipped |
| GET | `/api/v1/routines/history` | Bearer | 200, 401, 404 | List routine versions; pagination |

Error codes: `NO_HOUSEHOLD`, `NO_LOCATION`, `NO_MEMBERS`, `NO_ACTIVITIES`, `INVALID_WINDOW`, `INVALID_VENUE`, `UNKNOWN_MEMBER`, `FIXED_ACTIVITY_OVERLAP`, `TOO_MANY_ACTIVITIES`, `FORECAST_COVERAGE`, `ROUTINE_SUPERSEDED`, `DATE_MISMATCH`, `STALE_ENGINE_VERSION`.

---

### Impact Ledger — `/api/v1/impact`

| Method | Path | Auth | Status codes | Contract notes |
|--------|------|------|-------------|----------------|
| GET | `/api/v1/impact/factors` | Public | 200, 429 | Versioned factor registry; only factors with verifiable sources listed |
| GET | `/api/v1/impact/activities` | Bearer | 200, 401, 422 | List logged activities; `days`/`limit`/`offset` pagination |
| POST | `/api/v1/impact/activities` | Bearer | 201, 401, 409, 422 | Log activity; unverified types rejected `FACTOR_NOT_AVAILABLE`; duplicates `DUPLICATE_ACTIVITY` |
| GET | `/api/v1/impact/summary` | Bearer | 200, 401, 422 | Summarise logged impact over `days` |
| GET | `/api/v1/impact/baseline-savings` | Bearer | 200, 401, 422 | Modelled baseline vs logged activity; basis discloses assumption |
| GET | `/api/v1/impact/trends` | Bearer | 200, 401, 422 | Weekly/monthly trend buckets |
| GET | `/api/v1/impact/methodology` | Public | 200, 429 | Formulas, factors, assumptions, limitations |
| GET | `/api/v1/impact/goals` | Bearer | 200, 401, 422 | List sustainability goals |
| POST | `/api/v1/impact/goals` | Bearer | 201, 401, 422 | Create goal; unit must match activity type |
| PUT | `/api/v1/impact/goals/{goal_id}` | Bearer | 200, 401, 422 | Update goal; 422 `GOAL_NOT_FOUND` |
| DELETE | `/api/v1/impact/goals/{goal_id}` | Bearer | 204, 401, 422 | Delete goal |

Activity types: `walked`, `public-transport`, `worked-from-home`, `planted-tree`. Units: km, days, trees.

---

### Indoor Shield — `/api/v1/indoor`

| Method | Path | Auth | Status codes | Contract notes |
|--------|------|------|-------------|----------------|
| POST | `/api/v1/indoor/assessments` | Bearer | 201, 401, 404, 422 | Create assessment |
| GET | `/api/v1/indoor/assessments` | Bearer | 200, 401, 404 | List assessments |
| GET | `/api/v1/indoor/assessments/{id}` | Bearer | 200, 401, 404 | Read assessment |
| PUT | `/api/v1/indoor/assessments/{id}` | Bearer | 200, 401, 404, 422 | Update assessment |
| DELETE | `/api/v1/indoor/assessments/{id}` | Bearer | 204, 401, 404 | Delete assessment |
| POST | `/api/v1/indoor/assessments/{id}/refresh` | Bearer | 200, 401, 404, 503 | Refresh assessment with latest outdoor data |
| GET | `/api/v1/indoor/sensors` | Bearer | 200, 401, 404 | List registered sensors |
| POST | `/api/v1/indoor/sensors` | Bearer | 201, 401, 404, 422 | Register sensor |
| DELETE | `/api/v1/indoor/sensors/{id}` | Bearer | 204, 401, 404 | Deactivate sensor |
| POST | `/api/v1/indoor/sensors/{id}/readings` | Bearer | 201, 401, 404, 422 | Record sensor reading |
| GET | `/api/v1/indoor/sensors/{id}/readings` | Bearer | 200, 401, 404 | List sensor readings |
| POST | `/api/v1/indoor/assessments/{id}/actions/{action_id}/complete` | Bearer | 200, 401, 404 | Complete action |
| POST | `/api/v1/indoor/assessments/{id}/actions/{action_id}/reschedule` | Bearer | 200, 401, 404 | Reschedule action |
| POST | `/api/v1/indoor/assessments/{id}/actions/{action_id}/reopen` | Bearer | 200, 401, 404 | Reopen action |
| GET | `/api/v1/indoor/assessments/{id}/actions/{action_id}/events` | Bearer | 200, 401, 404 | List action events |
| POST | `/api/v1/indoor/assessments/{id}/explain` | Bearer | 200, 401, 404 | AI explanation with grounding validation |

---

### EcoRoute — `/api/v1/ecoroute`

| Method | Path | Auth | Status codes | Contract notes |
|--------|------|------|-------------|----------------|
| POST | `/api/v1/ecoroute/journeys` | Bearer | 201, 401, 404, 422 | Save journey with emission calculation |
| GET | `/api/v1/ecoroute/journeys` | Bearer | 200, 401, 404 | List journeys |
| GET | `/api/v1/ecoroute/journeys/{id}` | Bearer | 200, 401, 404 | Read journey |
| DELETE | `/api/v1/ecoroute/journeys/{id}` | Bearer | 204, 401, 404 | Delete journey |
| GET | `/api/v1/ecoroute/factors` | Public | 200, 429 | Emission factors for transport modes |
| GET | `/api/v1/ecoroute/compare` | Public | 200, 422 | Compare modes for origin/destination |

---

### Air Quality — `/api/v1/air-quality`

| Method | Path | Auth | Status codes | Contract notes |
|--------|------|------|-------------|----------------|
| GET | `/api/v1/air-quality/current` | Bearer | 200, 401, 404, 503 | Current reading with CPCB AQI and provenance |
| GET | `/api/v1/air-quality/forecast` | Bearer | 200, 401, 404, 503 | Hourly forecast |
| GET | `/api/v1/air-quality/history` | Bearer | 200, 401, 404 | Daily history |
| GET | `/api/v1/air-quality/providers` | Public | 200 | Provider health status |

---

### Locations — `/api/v1/locations`

| Method | Path | Auth | Status codes | Contract notes |
|--------|------|------|-------------|----------------|
| GET | `/api/v1/locations` | Bearer | 200, 401, 404 | List geocoded locations |
| POST | `/api/v1/locations/search` | Bearer | 200, 401, 422 | Search locations by query |

---

### Health — `/api/v1/health`

| Method | Path | Auth | Status codes | Contract notes |
|--------|------|------|-------------|----------------|
| GET | `/api/v1/health` | Public | 200 | Liveness/readiness; includes DB connectivity |
| GET | `/api/v1/health/ready` | Public | 200, 503 | Readiness check |

---

### Copilot — `/api/v1/copilot`

| Method | Path | Auth | Status codes | Contract notes |
|--------|------|------|-------------|----------------|
| POST | `/api/v1/copilot/chat` | Bearer | 200, 401, 422, 503 | Chat with grounded AI copilot; FactPack scoped to session |
| POST | `/api/v1/copilot/tool-request` | Bearer | 200, 401, 403, 422 | Execute authorized tool; `air_service` injected |

---

## Frontend API Client Surface

| Module | Functions | Schema validation | Error handling |
|--------|-----------|-------------------|----------------|
| `features/api/client.ts` | `apiData`, `apiDelete`, `apiRequest` | Zod schema on response | `ApiError` with status, code, requestId |
| `features/family/api.ts` | `fetchFamilyProfile`, `createFamilyProfile`, `replaceFamilyProfile`, `deleteFamilyProfile`, `fetchFamilyPreferences`, `replaceFamilyPreferences`, `generateFamilyRecommendations`, `fetchFamilyRecommendations`, `fetchFamilyRecommendation` | All responses validated with Zod schemas from `schema.ts` | 404 on profile = null (first-run, not error); other errors propagate as `ApiError` |
| `features/air-quality/api.ts` | `useAirCurrent`, `useAirForecast`, `useAirHistory`, `fetchLocationSearch` | Zod schemas | `classifyApiFailure` maps status → unavailable/error state |
| `features/session/use-session.ts` | `start`, `grantHealthConsent`, `deleteSession`, `clear` | Session schemas | Errors propagate to caller |
| `features/store/storage.ts` | `readStored`, `writeStored`, `removeStored`, `useStoredState` | Zod schema on read | Malformed JSON/schema mismatch → fallback |

---

## Contract Compliance Findings

1. **Envelope consistency:** All backend responses wrap data in `{ data, meta: { request_id } }`. ✓
2. **Error code consistency:** All errors use `{ type, title, status, detail, code, request_id }` with stable `code` strings. ✓
3. **Auth scoping:** All user-data routes require bearer token; public routes (factors, methodology, health) do not. ✓
4. **Rate limiting:** Session-scoped and IP-scoped rate limits on write-heavy routes. ✓
5. **Frontend schema validation:** All API responses validated with Zod before use. ✓
6. **Missing profile = first-run, not error:** Frontend treats 404 on `/family/profile` as null profile (first-run). ✓
7. **Health flags require consent:** Both backend (403 `CONSENT_REQUIRED`) and frontend (form-level validation) enforce this. ✓

No contract violations were found that require code changes.
