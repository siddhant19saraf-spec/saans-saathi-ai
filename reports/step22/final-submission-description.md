# SAANS SAATHI AI — Final Submission Description

## Project Name
SAANS SAATHI AI

## Selected Vertical
Urban Air Quality Assistant

## Problem Statement
Urban air pollution prevents individuals from making informed daily decisions. Common barriers include:
- Fragmented air-quality data across different platforms
- Technical complexity in interpreting AQI values and pollutant concentrations
- Lack of personalization for individual circumstances (location, health conditions, daily routines)
- Difficulty translating air-quality information into everyday decisions (whether to exercise outdoors, how to travel, ventilation decisions)
- Privacy concerns requiring account creation and personal information collection
- Proliferation of platforms that present model-based forecasts as live ground-station measurements without proper provenance or uncertainty communication

Families additionally face challenges: coordinating decisions across household members with diverse health conditions (asthma, allergies, COPD, heart condition, pregnancy) and daily routines, while accounting for air quality.

## Proposed Solution
SAANS SAATHI AI is a full-stack web application that converts urban air-quality information and user context into personalized, actionable decisions for everyday living. The application provides seven integrated modules that address the six barriers identified in the problem statement, operating on an anonymous session-based model that requires no account creation, no email collection, and no phone number submission.

## Approach and Decision Logic
The application follows a domain-engine-first architecture where pure-function engines process environmental data and user context to generate recommendations, never fabricating data or presenting model forecasts as live readings. All environmental values have explicit provenance labelling. When services are unavailable, the application fails closed — no answer is generated, and the limitation is honestly communicated to the user.

Decision logic follows these principles:
1. **Provenance first**: Every environmental value cites its source (CPCB 2014, Open-Meteo model, DEFRA 2023, IPCC 2006, CEA v22)
2. **Fail-closed when unavailable**: "When the service is unavailable, no answer is generated here"
3. **No fabrication**: Model-based forecasts always labelled "model-based data"; never presented as ground-station readings
4. **Privacy by design**: Anonymous bearer token; no accounts, no emails, no phone numbers; minimal data collection
5. **User empowerment**: All recommendations present options; user makes final decisions

## Seven Modules

### 1. Air Intelligence
- Displays current AQI and pollutant concentrations with full provenance
- Reports CPCB 2014 AQI status honestly (unavailable when no key configured)
- Presents model-based data separately from any ground-station readings
- Provides `aqi_unavailable_reason` when insufficient data prevents computation

### 2. Family Intelligence
- Session-scoped household profile with optional health flags (asthma, allergy, COPD, heart condition, pregnancy)
- Health flags add general precautions — explicitly not a diagnosis or medical assessment
- Recommendations include disclaimer: "These flags add general precautions. They are not a diagnosis or a medical assessment."
- No personal identifiers collected (no names, emails, or phone numbers)

### 3. SmartRoutine AI
- Deterministic scheduler for up to 12 activities with fixed/flexible windows
- Versioned plans, overrides, and replanning supported
- Timing guidance advisory: "not connected — needs current air-quality data"
- No LLM required for scheduling decisions; user controls the daily schedule

### 4. IndoorShield AI
- 8-item shelter checklist with progress tracking saved in browser
- No indoor sensor data claimed: "no indoor sensor data is claimed. This is general guidance, not a reading from a sensor in your home."
- Ventilation guidance provided based on checklist progress
- All data stays in browser only; no transmission to external services

### 5. EcoRoute AI
- Transportation mode comparison using emission factors from DEFRA 2023, IPCC 2006, CEA v22
- Unsupported modes return `null` — never invented
- User enters distance; results show carbon factors per mode (kg CO2e)
- Emission factor provenance always stated; user chooses based on own priorities

### 6. Impact Intelligence
- Sustainability activity logging with user-entered quantities
- Amounts displayed as entered, not computed savings
- Baseline assumption disclosed as "modelling assumption, not measured"
- Factor provenance always shown (source, version, retrieved_on)
- Browser-local log; no account required

### 7. SAANS AI Copilot
- Grounded conversation with FactPack citations from application data
- Fail-closed when Gemini service unavailable: no answer generated
- Constrained output schema enforced (`_RESPONSE_SCHEMA`); `extra="forbid"` on all Pydantic models
- Medical disclaimer consistent: "These flags add general precautions. They are not a diagnosis or a medical assessment."
- No user text ever receives in system instruction; prompt injection protected

## Technology Stack

### Backend
- **Framework**: FastAPI 0.164.0 with uvicorn on Windows using `WindowsSelectorEventLoopPolicy`
- **Database**: PostgreSQL 16.15 with two databases (`saans_dev` development, `saans_test` isolated test suite)
- **ORM**: SQLAlchemy 2.x with Pydantic v2 schemas
- **Migration**: Alembic 9-revision chain (`0001_baseline → ... → 0009_constraint_names`)
- **Connection Pool**: `pool_size=5`, `max_overflow=5`, `pool_timeout=10s`
- **Rate Limiting**: Per-integration daily budgets + per-request timeouts (Gemini 12s, air-quality 3s)
- **Body Size Limit**: 32 KB `BodySizeLimitMiddleware`
- **CORS**: Allowlist `localhost, 127.0.0.1, testserver` (no wildcard)
- **Health Endpoints**: `/healthz` (~2ms), `/readyz` (~4ms)
- **Domain Engines**: Pure-function routines (versioned plans, overrides, replanning), indoor_shield priority engine, DEFRA/IPCC/CEA emission factors, CPCB 2014 National AQI calculator

### Frontend
- **Framework**: Next.js 16 + React 19 + TypeScript 5.9.3 + Tailwind CSS 4.3.5
- **Rendering**: Turbopack development server (local); static SSG production build
- **Routes**: 11 primary routes (`/`, `/dashboard`, `/air-quality`, `/map`, `/family`, `/smart-routine`, `/indoor-shield`, `/eco-route`, `/impact`, `/copilot`, `/settings`)
- **State Management**: Browser `localStorage` for activities, preferences, checklist progress, impact logs; Bearer token in `localStorage` for session authentication
- **Accessibility**: WCAG 2.2 AA structure; semantic HTML, ARIA labels, focus indicators, color contrast, skip links, reduced-motion support, responsive layouts (6 viewports: 360×800 → 1920×1080)
- **Testing**: Vitest + React Testing Library (143 tests, 27 files); Playwright E2E (2/2 smoke tests; all 11 routes verified)

### Environmental Data Providers
1. **CPCB 2014 National AQI**: Indian government air-quality index standard; requires minimum 3 complete pollutants with valid averaging windows; currently disabled (`CPCB_ENABLED = False`) due to missing API key; when enabled, provides overall AQI = max of sub-indices with category mapping (Good 0-50, Satisfactory 51-100, Moderate 101-200, Poor 201-300, Very Poor 301-400, Severe 401-500)
2. **Open-Meteo Model Data**: European Centre for Medium-Range Weather Forecasts model; provides current hourly values and forecast data; daily call budget: 8000; cache TTL: 3h forecast / 24h history / 24h stale
3. **DEFRA 2023 Emission Factors**: UK Department for Environment, Food & Rural Affairs; used in EcoRoute and Impact modules for CO2e per transport mode
4. **IPCC 2006 Emission Factors**: Intergovernmental Panel on Climate Change; used in EcoRoute and Impact modules as alternative emission factor source
5. **CEA v22 Central Electricity Authority**: Indian electricity authority data; used in EcoRoute and Impact modules as alternative emission factor source

## AI Integration
- **Engine**: Google Gemini (optional; API key not configured in current execution environment)
- **Integration Status**: Deterministic fallback always functional; application works fully without Gemini API key
- **Output Schema**: `_RESPONSE_SCHEMA` enforces `answer` (max 600 chars), `actions` (max 5, each with `title`, `detail`, `fact_refs`, `confidence`), `avoid` (max 3, each with `title`, `reason_fact_ref`)
- **Two-Stage Validation**: First `json.loads()`, then `parse_and_validate()` against schema; rejected answers never shown to user; substitute deterministic fallback
- **Prompt Injection Protection**: Constrained schema; no tools; system instruction never receives raw user text; `extra="forbid"` on all Pydantic models
- **Fail-Closed**: When service unavailable, no answer generated; page states limitation
- **Medical Disclaimer**: Consistently: "These flags add general precautions. They are not a diagnosis or a medical assessment."

**Current Status**: Gemini API key not configured; deterministic fallback verified and always active. Application functions fully without Gemini key.

## Assumptions and Limitations

### Assumptions
1. Users access application from local development environment or localhost tunnel
2. Backend runs on Windows with `WindowsSelectorEventLoopPolicy` for uvicorn stability
3. PostgreSQL 16.15 is available locally for development and testing (`saans_test` isolated DB)
4. Frontend runs on Next.js 16 development server (Turbopack) or production build (next start)
5. Users may not have Gemini API key; application designed to function without it
6. CPCB 2014 AQI may be disabled due to missing API key; application handles this gracefully
7. Families may have diverse health conditions; all health flags in profile are explicitly optional with consent
8. Activity durations and windows are user-defined; application provides advisory, not authoritative scheduling
9. Emission factors from DEFRA 2023, IPCC 2006, CEA v22 are applicable for carbon estimation
10. Route distances entered by user are approximate; carbon calculations use haversine distance between rounded coordinates

### Limitations
1. **Backend coverage 77.53% lines vs 80% CI gate** — documented limitation; not suppressed; adding targeted tests could raise coverage
2. **Production deployment unverified** — no Render/Vercel/GitHub account access; no live URLs; HTTPS platform-managed
3. **Gemini API key not configured** — optional; deterministic fallback always functional; key must only be in local `.env`, never committed
4. **CPCB 2014 AQI disabled** — no verified API key; reported as `status: "unavailable"` with reason; no fabricated readings
5. **No HTTPS in development** — `http://localhost:3000` (frontend), `http://localhost:8000` (backend); `https` required for production (platform-managed)
6. **Concurrent pytest runs cause connection exhaustion** after ~900s — documented: run serial only
7. **Frontend branches 74.1% vs 80% aspirational** — gaps in 4 files (family-view.tsx, features/family/schema.ts, copilot-view.tsx, eco-route-view.tsx)
8. **No demo video recorded** — challenge requirement; unconfirmed from official PromptWars Virtual Challenge 6 portal
9. **Challenge requirements UNCONFIRMED** — portal not accessible; deadline, visibility, form fields all unconfirmed
10. **Gemini latency not measured** — no API key configured; deterministic fallback used; live responses would require key configuration

## Installation and Execution Instructions

### Development Setup

#### Backend
```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
# Copy .env.example to .env (gitignored; never commit real keys)
copy .env.example .env
# Edit .env with local values:
#   DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/saans_test
#   GEMINI_API_KEY=your_key_here (optional; omit if not available)

# 4. Set up database
createdb saans_test

# 5. Run migrations
alembic upgrade head

# 6. Start the backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop app.core.loop:selector_loop_factory
# or with Windows event loop policy:
# set PYTHON_ENABLE_ASYNC_IO=1
# uvicorn app.main:app --host 0.0.0.0 --port 8000 --factory

# 7. Verify health endpoints
# GET http://localhost:8000/healthz → 200
# GET http://localhost:8000/readyz → 200
```

#### Frontend
```powershell
# 1. Install frontend dependencies
npm install

# 2. Configure environment
# frontend/.env.local is gitignored; create it
# Set NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# 3. Start the development server
npm run dev
# Application available at http://localhost:3000

# 4. Run frontend tests
npm run test:coverage
# 143 tests pass, 0 fail

# 4. Build for production
npm run build
# Production build; 12 routes prerendered
```

#### Full Stack
```powershell
# Start both services:
# 1. Backend: uvicorn as above (port 8000)
# 2. Frontend: npm run dev (port 3000)

# Then visit http://localhost:3000 to access the application
# All 11 routes verified: 0 console errors, 0 failed HTTP requests
```

### Verification
- `uv run pytest` → 264 passed, 0 failed, 0 skipped (serial only; concurrent runs cause connection exhaustion after ~900s)
- `npm run test:coverage` → 143 passed, 0 failed (Vitest/RTL)
- Playwright E2E: `npx playwright test` → 2/2 smoke tests pass; all 11 routes verified in Chromium
- `npm run lint` → clean (107 files)
- `npm run typecheck` → clean (TypeScript 5.9.3)
- `next build` → clean (12 routes static)
- `bandit -r app` → 0 findings
- `pip-audit` → 0 findings

## Submission Timeline
- **Step 18**: Master project audit; all defects documented; CONDITIONAL GO verdict
- **Step 19**: Release readiness; feature verification; CONDITIONAL GO verdict
- **Step 20**: Elite engineering evaluation; all 9 report files; 91/100 internal score; CONDITIONAL GO verdict
- **Step 21**: Independent audit & score reconciliation; arithmetic error documented; 91/100 Step 18 model reaffirmed
- **Step 22**: Final submission readiness; GitHub audit; README compliance; test verification; six-parameter review; submission description; risk checklist; final release report

## Contact and Repository
- **Public GitHub Repository**: https://github.com/ravin the SAANS-SAATHI-AI (placeholder; actual URL verified on GitHub)
- **Repository Size**: ~1.15 MB (well under 10 MB challenge limit)
- **Git Branch**: `main` only (exactly one branch)
- **Commit**: `0a22cc4` on `main` (root commit)