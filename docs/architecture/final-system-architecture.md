# SAANS SAATHI AI — Final System Architecture

## Mermaid Diagram

```mermaid
flowchart TD
    %% Styles
    classDef user fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef frontend fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef backend fill:#fff3e0,stroke:#fb8c00,stroke-width:2px
    classDef database fill:#bbdefb,stroke:#039be5,stroke-width:2px
    classDef engine fill:#f1c40f,stroke:#f39c12,stroke-width:2px
    classDef ai fill:#fce4ec,stroke:#ad1457,stroke-width:2px
    classDef provider fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,dashed

    %% Actors
    USER[User<br/>(Browser / Mobile)]:::user

    %% Frontend
    NEXT[Next.js 16 Frontend<br/>Turbopack Dev / Prod Build]:::frontend
    STYLE NEXT:fill-width:400px

    %% Backend
    FASTAPI[FastAPI Application<br/>uvicorn + WindowsSelectorEventLoopPolicy]:::backend
    STYLE FASTAPI:fill-width:400px

    %% Database
    PG[(PostgreSQL 16.15<br/>saans_dev / saans_test)]:::database
    STYLE PG:fill-width:250px

    %% Domain Engines
    ROUTINED[routine-2.0.0 Scheduler<br/>Deterministic plan generation]:::engine
    INDOOR[indoor-shield-1.0.0 Priority Engine]:::engine
    EMISSION[DEFRA 2023 / IPCC 2006 / CEA v22]:::engine
    AQICalc[CPCB 2014 National AQI Calculator]:::engine
    STYLE AQICalc:fill-width:300px

    %% Data Providers
    OPENOMETOE[Open-Meteo<br/>Model forecasts, current, history]:::provider
    CPCB[CPCB 2014 Data Gov.in<br/>National AQI (currently disabled)]:::provider
    GEOCODE[Open-Meteo Geocoding]<:::provider

    %% AI
    GEMINI[Google Gemini API<br/>Constrained via FactPack + Schema]:::ai
    STYLE GEMINI:fill-width:350px

    %% Connections
    USER -->|HTTP, HTTPS| NEXT
    NEXT -->|API calls (REST/JSON)| FASTAPI
    FASTAPI -->|SQLAlchemy ORM| PG
    FASTAPI -->|Pure-function calls| ROUTINED
    FASTAPI -->|Pure-function calls| INDOOR
    FASTAPI -->|Emission factor lookups| EMISSION
    FASTAPI -->|AQI sub-index computation| AQICalc
    FASTAPI -->|REST calls| OPENOMETOE
    FASTAPI -->|REST calls (attempted)| CPCB
    FASTAPI -->|Geocoding calls| GEOCODE
    FASTAPI -->|Constrained REST| GEMINI
    GEMINI -->|Validated JSON (answer, actions, avoid)| FASTAPI
    OPENOMETOE -->|Model forecasts (current, history, forecast)| FASTAPI
    CPCB -->|AQI values (when available)| FASTAPI
    GEOCODE -->|Location search results| FASTAPI

    %% Sub-module connections within Backend
    ROUTINED -->|Activity scheduling, override/replanning| FASTAPI
    INDOOR -->|Checklist assessment, ventilation guidance| FASTAPI
    EMISSION -->|CO2e calculations, emission factors| FASTAPI
    AQICalc -->|Sub-index, overall AQI, unavailable reasons| FASTAPI

    %% Styling adjustments
    classDef moduleIcon fill:#fff,stroke:none;padding:4px;border-radius:2px
```

---

## Architecture Description

### 1. User Layer
- **Interface**: Next.js 16 application accessible via browser (desktop/mobile)
- **Access**: Anonymous — no account creation, no authentication required
- **Entry points**: 7 module CTA links from landing page; direct route navigation

### 2. Frontend Layer
- **Framework**: Next.js 16 + React 19 + TypeScript + Tailwind CSS
- **Rendering**: Turbopack development server (local); static SSG production build
- **Routes**: 11 primary routes (`/`, `/dashboard`, `/air-quality`, `/map`, `/family`, `/smart-routine`, `/indoor-shield`, `/eco-route`, `/impact`, `/copilot`, `/settings`)
- **State Management**: 
  - Browser `localStorage` for activities, preferences, checklist progress, impact logs
  - Bearer token in `localStorage` for session authentication (SHA-256 digest verified in backend)
  - No global state management library; React useState/useEffect hooks per page
- **Accessibility**: WCAG 2.2 AA structure; semantic HTML, ARIA labels, focus indicators, color contrast, skip links, reduced-motion support, responsive layouts (6 viewports)

### 3. Backend Layer
- **Framework**: FastAPI 0.164.0 with uvicorn on Windows with `selector_loop_factory`
- **Event Loop**: `WindowsSelectorEventLoopPolicy` — required for uvicorn stability on Windows (proactor-style default incompatible with Windows)
- **Database**: PostgreSQL 16.15 with two databases:
  - `saans_dev`: Development data
  - `saans_test`: Isolated test suite (`TEST_DATABASE_URL`)
- **ORM**: SQLAlchemy 2.x with Pydantic v2 schemas
- **Migration**: Alembic 9-revision chain; `0009_constraint_names` fixes 8 check-constraint name drifts
- **Connection Pool**: `pool_size=5`, `max_overflow=5`, `pool_timeout=10s`
- **Rate Limiting**: Per-integration budgets (`ai_daily_request_budget=300`, `openmeteo_daily_call_budget=8000`, `openaq_daily_call_budget=2000`) + per-request timeouts (12s Gemini, 3s air-quality, 24h geocaching cache TTL)
- **Body Size Limit**: 32 KB `BodySizeLimitMiddleware` — rejected before handler execution

### 4. Domain Engines (Pure Functions)
All business logic resides in pure-function domain engines — no state, no side effects, fully testable:

- **routine-2.0.0 scheduler**: Versioned plans, overrides, replanning, activity preference validation; deterministic activity ordering by start timezone-aware time
- **indoor-shield-1.0.0 priority engine**: 8-item shelter checklist, ventilation guidance, explicit "no indoor sensor data is claimed" disclaimer
- **DEFRA 2023 / IPCC 2006 / CEA v22 emission factors**: Used in EcoRoute and Impact modules; unsupported activity types → `None` (never invented)
- **CPCB 2014 National AQI calculator**: Sub-index computation from pollutant sub-indices; overall AQI = max of sub-indices; category mapping (Good 0-50, Satisfactory 51-100, Moderate 101-200, Poor 201-300, Very Poor 301-400, Severe 401-500); requires minimum 3 complete pollutants with valid averaging windows (24-hr: 16 valid hours min for PM2.5/PM10; 8-hr: 6 valid hours min for NO₂/SO₂/CO/O₃); incomplete data → `aqi_unavailable_reason` explained

### 5. External Data Providers

- **Open-Meteo**: Model-based forecasts (current, historical, 3-day forecast); cache TTL 30s current / 3h forecast / 24h history / 24h stale; used for air-quality current values and forecast data; always labelled "model-based data"
- **CPCB 2014 Data Gov.in**: India National AQI source (currently disabled `CPCB_ENABLED = False`); no verified data-access endpoint; reported as `status: "unavailable"` with `aqi_unavailable_reason`; never mixed with US/European scales
- **Open-Meteo Geocoding**: Location search cache TTL 24h; used for map location search; returns rounded coordinates

### 6. AI Orchestration (Google Gemini)

- **Integration**: Optional REST adapter; not configured in current environment (API key missing)
- **Isolation**: 
  - No tools — Gemini has no function-call capabilities
  - System instruction never receives user text — user input goes to `user` role only in conversation history
  - Constrained output schema (`_RESPONSE_SCHEMA`): `answer` (max 600 chars), `actions` (max 5, each with `title`, `detail`, `fact_refs`, `confidence`), `avoid` (max 3, each with `title`, `reason_fact_ref`)
  - `extra="forbid"` on all Pydantic models (`DraftAction`, `DraftAvoid`, `AiDraft`) — Gemini output violating this rejected via `parse_and_validate()`
  - Two-stage validation: `json.loads()` → `parse_and_validate()` against `AiDraft` model
  - Fail-closed: when service unavailable, no answer generated; page explicitly states "When the service is unavailable, no answer is generated here"
- **Grounding**: FactPack built from application data only (no independent AQI calculation, no sensor invention, no emission factor invention, no route invention, no savings invention, no medical diagnosis)
- **Prompt injection protection**: Constrained JSON schema blocks injection vectors; system instruction isolation prevents user text from influencing system prompt

### 7. Database Layer

- **PostgreSQL 16.15** on local development machine
- **Two databases**:
  - `saans_dev`: Development; used by uvicorn in `--loop app.core.loop:selector_loop_factory`
  - `saans_test`: Isolated test suite; `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/saans_test`
- **9 Alembic revisions**: `0001_baseline → 0002_initial_schema → 0003_integrity_constraints → 0004_air_source_types → 0005_family_intelligence → 0006_smart_routine → 0007_indoor_shield → 0008_ecoroute_impact → 0009_constraint_names`
- **Models**: `air`, `household`, `impact`, `indoor`, `profile`, `profile_member`, `routine`
- **Session model**: Anonymous bearer token (SHA-256 digest); no user accounts, no emails, no phone numbers
- **Ownership**: Session-scoped — one profile per anonymous bearer token; no cross-user access possible

### 8. Data Flow Summary

1. **User navigates** to a route (e.g., `/family`)
2. **Frontend fetches** data via typed API client (`api/client.ts`) with Zod schema validation
3. **Backend receives** request; validates via Pydantic v2 schemas
4. **Domain engine** processes request (e.g., `indoor_shield_service.py` for IndoorShield)
5. **Database** reads/writes session-scoped data (if applicable)
6. **Provider calls** made if needed (Open-Meteo model data; CPCB disabled)
7. **Response** returned to frontend with full provenance
8. **AI may assist** (Copilot only) — FactPack grounded in application data; fail-closed when unavailable
9. **Frontend renders** with semantic HTML, ARIA labels, focus indicators, color contrast
10. **User interaction** — form submissions, activity additions, assessments, logging
11. **Cycle repeats** for each user action

### 9. Authentication & Session Management

- **Model**: Anonymous bearer token
- **Flow**:
  1. `POST /api/v1/sessions` → creates session; response includes `bearer_token`
  2. Browser stores `bearer_token` in `localStorage`
  3. All subsequent API requests include `Authorization: Bearer <token>`
  4. Backend validates token SHA-256 digest against PostgreSQL `sessions` table
  5. Session auto-expires; `DELETE /api/v1/sessions/me` deletes profile, household, preferences, saved locations, recommendations
- **Ownership**: Session-scoped only — one profile per token; no user accounts, no names, no emails

### 10. Error Handling

- **All API errors**: RFC 9457 format `{type, title, status, detail, request_id}`
- **No stack traces** exposed to users
- **No PII** in error messages
- **Database transactions**: Roll back on error (SQLAlchemy session handling)
- **Provider failures**: Graceful degradation; `aqi_unavailable_reason`; `status: "unavailable"`; no fabricated readings
- **Gemini unavailability**: Fail-closed — "When the service is unavailable, no answer is generated here"
- **Validation errors**: Field-scoped messages via `FieldError` component; `aria-invalid` + `aria-describedby` on form controls

### 11. Key Boundaries (Non-Negotiable)

| Boundary | Implementation |
|----------|----------------|
| **No fabricated environmental data** | All values have provenance; unavailable data has explicit reason; never shown as live readings |
| **No mixed AQI standards** | CPCB 2014 National AQI kept separate; never remapped onto US/European scales |
| **No AQI from single pollutant** | Requires minimum 3 complete pollutants with valid averaging windows |
| **Gemini must not calculate AQI** | Deterministic backend `evaluate_cpcb_aqi()` handles all AQI computation |
| **Gemini must not invent sensor data** | FactPack built from application data only; no sensor data in prompts |
| **Gemini must not invent emission factors** | DEFRA/IPCC/CEA factors sourced from backend; `None` for unsupported modes |
| **Fail-closed AI** | When service unavailable, no answer generated; page states limitation |
| **Privacy by design** | Anonymous sessions; minimal data collection; deletion controls; no PII |
| **No color-only information** | Icons + text always combined; never color-only to convey meaning |
| **WCAG 2.2 AA compliance** | Target throughout; semantic HTML, ARIA, focus indicators, contrast, skip links |

---

## Diagram Conventions

- **Solid arrows**: Primary request/response data flow
- **Dashed arrows**: Optional/provider-dependent flow
- **Color coding**: 
  - **User** (blue): Human actor
  - **Frontend** (green): Next.js client
  - **Backend** (orange): FastAPI service
  - **Database** (purple): PostgreSQL
  - **Engines** (yellow): Pure-function domain logic
  - **AI** (pink): Google Gemini (optional)
  - **Providers** (light blue): External data sources (dashed = currently disabled/unverified)

---

*Architecture diagram generated as part of Step 19 — Final Repository Audit and Release Preparation on 2026-11-22.*
*For the most current architecture, refer to the codebase and live documentation.*