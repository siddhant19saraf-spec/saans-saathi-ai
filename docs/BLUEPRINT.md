# SAANS SAATHI AI — Engineering Blueprint (Step 1)

**Project:** Smart Air Quality & Sustainable Living Intelligence Assistant
**Challenge:** Hack2Skill PromptWars Virtual — Challenge 6, Urban Air Quality Assistant
**Document status:** Step 1 deliverable. No application code, dependencies or files beyond this document have been created.
**Research verified on:** 2026-11-18 (all "Verified" claims below were checked against live endpoints or official docs on this date)
**Approval required before Step 2.**

---

## 0. Executive summary

SAANS SAATHI AI is a decision-support product, not a dashboard. Its value is a defensible answer to
*"What should my family do differently today, and why?"* — grounded in measured/modelled air-quality
data, household context, and transparent physics/emission arithmetic.

Three architectural commitments drive every other decision:

1. **Deterministic core, AI as narrator.** All numbers — AQI, exposure dose, indoor estimates,
   carbon, schedules — are computed by pure, unit-tested Python functions from a `FactPack`.
   Gemini receives the FactPack and may only *phrase* and *prioritise* it. It never produces a
   number that the engine did not compute. If Gemini is unavailable, the product still works, with
   deterministic templates and a visible "AI unavailable" label.
2. **Honest data provenance.** The UI never presents modelled CAMS output as a local sensor
   reading, never interpolates a missing pollutant, and never shows a number when the provider
   failed. Every screen carries source, observation time, age and staleness state.
3. **Small surface, strong gates.** One branch, no Redis, no microservices, no auth provider.
   Quality is enforced by CI (types, lint, format, unit, integration, a11y, secret scan, size check)
   rather than by convention.

**Biggest external finding:** the Gemini free tier in late 2026 is narrow and volatile
(secondary sources report 20–500 requests/day depending on model; Google does not publish a stable
table in the rendered docs). The product therefore treats AI as an *optional enhancement with a
hard daily budget*, not as a dependency. See §2.5 and §8.

**Second finding, measured live:** for Delhi on 2026-11-18 22:30 IST, Open-Meteo returned
PM2.5 = 75.2 µg/m³. The provider's US AQI was 166 ("Unhealthy"), while the CPCB index computed from
the same concentrations is ≈151 ("Moderate"). Presenting "AQI" without naming the scale would
mislead Indian users by ~1 category band. The product computes and labels **CPCB AQI** as primary
and shows other indices only as clearly labelled secondary values.

---

## 1. Problem analysis

### 1.1 Who the product is for

| Persona | Context | Job to be done | Failure mode today |
|---|---|---|---|
| Urban parent (Delhi, Mumbai, Kolkata, Bengaluru) | 2–5 person household, school run, commute | "Is it safe for my child to play outside at 6pm, and if not, what do we do instead?" | Generic city AQI number with no household context and no alternative action |
| Health-sensitive adult (asthma, COPD, older adult) | Needs to plan exposure, not diagnose it | "When is the cleanest 2-hour window for my walk?" | Hourly graphs without interpretation |
| Cost-conscious household | LPG/PNG cooking, occasional purifier use | "Do I need a purifier, what size, and when?" | Marketing-driven advice, no room-volume maths |
| Sustainability-minded commuter | 5–20 km daily trip | "Which mode is better for my lungs and for emissions?" | Carbon calculators that ignore exposure; route apps that ignore air |

### 1.2 The real problem (and what we deliberately do not solve)

The problem is **decision latency under uncertainty**, not data scarcity. Users already have AQI
numbers; they lack a household-specific, forecast-aware, *actionable* plan with an explanation.

Non-goals, stated explicitly to protect quality:
- No medical diagnosis or treatment advice. Output is behavioural guidance with a persistent
  non-medical disclaimer (§12.9).
- No regulatory-grade AQI reporting. We compute CPCB AQI from provider concentrations for
  decision support and label the method and coverage.
- No live sensor hardware integration in v1.
- No turn-by-turn navigation. EcoRoute compares modes on estimated distances and states the
  distance source.

### 1.3 Success metrics (measurable, hackathon-compatible)

| Metric | Target | How measured |
|---|---|---|
| Time to first actionable answer | < 15 s from cold load on 4G | Lighthouse trace + manual stopwatch |
| Recommendation grounding | 100% of numeric claims traceable to a FactPack fact | Automated validator test suite |
| Data honesty | 0 screens rendering a value when provider data is absent | Negative-path Playwright tests with providers mocked down |
| Accessibility | axe: 0 critical/serious; Lighthouse a11y ≥ 95 | CI (`@axe-core/playwright`) |
| API latency | p95 < 400 ms cache hit, < 2.5 s cache miss | Structured logs + `/v1/meta` |
| Carbon transparency | 100% of factors carry `source_url` + version | Factor registry test |
| Repo hygiene | < 10 MB, 1 branch, 0 secrets | CI size + gitleaks gate |

---

## 2. Research findings (verified against official sources)

### 2.1 Research log

| Service | Official source | Verification method | Confirmed facts (2026-11-18) | Limits / risks | Role in product |
|---|---|---|---|---|---|
| Open-Meteo Air Quality | `air-quality-api.open-meteo.com/v1/air-quality`; open-meteo.com/en/docs/air-quality-api | Docs + **live call** | Variables `pm10, pm2_5, carbon_monoxide, nitrogen_dioxide, sulphur_dioxide, ozone, us_aqi, european_aqi`; hourly + `current`; units **µg/m³ for all pollutants incl. CO**; `forecast_days` ≤ 7; `past_days` 0–92; `start_date/end_date` archive; European reanalysis from 2013; global = CAMS forecast/recent past only | Modelled CAMS data (global ~11–40 km), **not** a local sensor; models update every 12–24 h; no SLA; free tier non-commercial | Primary air-quality provider |
| Open-Meteo terms | open-meteo.com/en/terms | Docs | Free: **<10,000 calls/day, 5,000/hour, 600/minute**. Commercial use requires subscription. Caching/storage not explicitly granted | Cache TTL must stay ≤ provider update interval; attribution mandatory | Quota budgeting + cache policy |
| Open-Meteo Geocoding | `geocoding-api.open-meteo.com/v1/search` | **Live call** | Returns `name, latitude, longitude, country_code, admin1, timezone, population`; no key | Best-effort; no SLA | Location search (server-side proxy) |
| OpenAQ v3 | `api.openaq.org/v3`; docs.openaq.org | Docs + quick-start | Auth via **`X-API-Key`** header; `/v3/locations`, `/v3/locations/{id}/latest`, `/v3/parameters`, `/v3/countries` (ISO-3166 alpha-2 filter); free tier **60/min, 2,000/hour**; attribution required | India station coverage and metadata quality **not yet verified** — must be checked with a key (`/v3/locations?country=IN`) | Optional secondary *measured* provider |
| CPCB / data.gov.in | data.gov.in resource `3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69` | Secondary sources + resource listing; **direct fetch returned 403** | Real-time AQI dataset published hourly by CPCB via data.gov.in; requires `api-key` query param; fields include station, city, pollutant id, average, `last_update` | **No official CPCB public REST API**; no SLA; historically intermittent; key required; CORS unsuitable for browsers | Optional "official station" provider, **off by default** |
| Gemini models | aistudio.google.com/docs/models | Docs | Stable Gemini 4 IDs: `gemini-4-carbon`, `gemini-4-argon`, `gemini-4-hydrogen` (1M context). Low-cost: `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.8-flash` | Model lineup changes monthly; IDs must be configuration, not code | Copilot |
| Gemini pricing | aistudio.google.com/docs/pricing | Docs | `gemini-3.5-flash-lite` **$0.30 / $2.50** per 1M in/out; `gemini-3.1-flash-lite` $0.25 / $1.50; `gemini-3.8-flash` $0.75 / $3.75; `gemini-4-hydrogen` $1.50 / $7.50; `gemini-4-argon/carbon` $2.00 / $10.00 (no free tier). Several prices increase 2026-12-01 | Cost rises imminently; free tier can disappear per model | Budgeting |
| Gemini rate limits | aistudio.google.com/docs/rate-limits | Docs (table partially rendered) + secondary | Free tier exists but is small and volatile; secondary sources report **≈20 RPD for some flash models, ≈500 RPD for 3.5 Flash-Lite**. Limits are per project | Cannot be relied on for a public demo | Design AI as optional |
| Gemini structured output | aistudio.google.com/docs/structured-output | Docs | `response_mime_type="application/json"` + JSON schema; server ignores `minLength/maxLength/uniqueItems/contains` etc.; subset of JSON Schema | Schema must be **re-validated with Pydantic** | Copilot output contract |
| Gemini Python SDK | pypi.org/project/google-genai (3.5.0) | Docs | `client.models.generate_content(model=..., contents=..., config=types.GenerateContentConfig(response_mime_type=..., response_json_schema=...))`; newer `client.interactions.create` + `response_format` also exists | Two API shapes in one SDK → adapter must pin one and smoke-test | Copilot client |
| CEA grid emission factor | CEA CO₂ Baseline Database v22.0 (Aug 2026), FY 2025-26 | Official PDF link + two independent secondary sources | All-India weighted average **0.675 tCO₂/MWh** (675 gCO₂/kWh) | PDF not machine-parsed here; **transcribe exact table row at implementation** | Electricity / EV / purifier carbon |
| CPCB National AQI | CPCB AQI methodology (2014), reproduced by ies.gov.in | Government source | Six bands and per-pollutant breakpoints (table in §10.1) | O₃ and CO averaging windows differ; must not mix 1 h and 8 h values | Primary severity index |
| WHO 2021 AQG | WHO global air quality guidelines (2021) | **Not machine-verified** (page did not render values) | Commonly cited: PM2.5 5 annual / 15 24 h; PM10 15 / 45; NO₂ 10 / 25; O₃ 60 peak / 100 8 h; SO₂ 40 24 h; CO 4 mg/m³ 24 h | Must transcribe from the WHO PDF before shipping; pinned by test | Health-context reference line on charts |
| DEFRA conversion factors | gov.uk GHG conversion factors 2025 | **Not verified** (XLSX/PDF not parseable in this session) | Transport factors are published per passenger-km | Do not ship unverified numbers | Optional benchmark only |
| OSM tiles | tile usage policy | Docs | Attribution required; no heavy/programmatic use | A public demo can be rate-limited or blocked | Map basemap with attribution + graceful fallback |
| OSRM demo server | `router.project-osrm.org` | **Live call** (17.6 km / 23.7 min for a Delhi pair) | Returns distance/duration; no key | Best-effort demo server, **no SLA**, explicitly not for production | Optional routing provider |

### 2.2 Live probe evidence

```
GET https://air-quality-api.open-meteo.com/v1/air-quality
    ?latitude=28.6139&longitude=77.2090
    &current=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi,european_aqi
    &hourly=pm2_5,us_aqi&forecast_days=1&timezone=Asia/Kolkata
→ current: pm2_5 75.2, pm10 76.4, carbon_monoxide 1581.0 (µg/m³), no2 63.7, so2 27.9, o3 26.0,
  us_aqi 166, european_aqi 73, interval 3600, time 2026-11-18T22:30
```

Consequences baked into the design:
- **CO arrives in µg/m³**, CPCB CO breakpoints are mg/m³ → divide by 1000. A unit test pins this.
- The response contains **no model-run timestamp**, only `current.time`. "Freshness" must be
  described as *fetch age* + "modelled forecast", never as sensor freshness.
- `current.time` is timezone-local (`utc_offset_seconds` supplied). All storage is UTC; all
  presentation is in the household timezone.
- Open-Meteo snaps to a grid point (28.599998 / 77.20001 for the requested 28.6139 / 77.2090).
  The snapped coordinates are part of the response contract and are surfaced to the user.

### 2.3 Data-quality reality that shapes the UX

| Reality | Product response |
|---|---|
| Global coverage is CAMS model output, ~11–40 km resolution | Label "Modelled (CAMS)" on every reading; never call it "live" |
| India CPCB data is station-level but has no stable official API | Optional provider behind a feature flag; when enabled, label "Official station, X km away, 14:00" |
| OpenAQ India coverage is partial | Corroboration only; never merged with modelled values |
| Historical depth outside Europe is limited to `past_days` ≤ 92 | History UI capped at 90 days with an explicit note; no synthetic backfill |
| Missing pollutants are common | `null` + "Not reported" per pollutant; AQI coverage list; no interpolation |

### 2.4 Licence and attribution obligations

- Open-Meteo: "clear attribution to CAMS ENSEMBLE data provider and reference Open-Meteo" — rendered
  in the footer of every air screen and in `meta.attribution` of every air response.
- OpenAQ: source attribution required per its Terms of Use.
- OpenStreetMap: "© OpenStreetMap contributors" on the map.
- CEA / WHO / CPCB: factor registry stores title, version, URL and retrieval date; the Impact
  screen links each factor to its source.

### 2.5 Explicitly unverified — must be verified at implementation

1. Exact Gemini free-tier RPM/TPM/RPD per model (rendered docs are incomplete; verify in AI Studio
   and by a 1-request smoke test). **Do not hard-code.**
2. Whether Gemini's free tier permits using prompts for product improvement — assume **yes** and
   therefore never send health flags, precise coordinates, or free-text household descriptions.
3. Whether Open-Meteo's terms permit storing responses — assume **no blanket permission**; cache
   only for ≤ 24 h and re-fetch.
4. OpenAQ India station coverage — query `/v3/locations?country=IN` with a key.
5. CPCB data.gov.in record schema and uptime — test with a key before enabling.
6. CEA v22.0 exact table row (0.675 tCO₂/MWh appears in secondary sources).
7. WHO 2021 AQG exact values — transcribe from PDF.
8. OSM tile policy suitability for a public demo.

---

## 3. Technology selection

### 3.1 Pinned versions (resolved 2026-11-18)

| Layer | Package | Version | Why this and not "newest" |
|---|---|---|---|
| Web framework | `next` | 16.4.6 | Current stable; App Router, RSC, route-level splitting |
| UI runtime | `react` / `react-dom` | 19.3.1 | Required by Next 16 |
| Language | `typescript` | **5.9.3** | TS 7.0.2 is GA but is the new native compiler; ecosystem/tooling risk in a 10-day build. 5.9.3 is fully supported by Next 16 (`peer typescript >=3.3.1`) |
| Styling | `tailwindcss` | 4.3.5 | CSS-first config; shadcn/ui compatible |
| Components | shadcn/ui (vendored) | current CLI | Owned source, no runtime dependency, accessible Radix primitives |
| Charts | `recharts` | 3.11.0 | SVG output → inspectable + accessible fallbacks |
| Validation | `zod` | 4.6.7 | Runtime boundary validation on the client |
| Maps | `leaflet` 1.9.4 / `react-leaflet` 5.0.0 | | Lightweight, OSM tiles, no key |
| Data fetching | `@tanstack/react-query` | 5.108.0 | Caching, retries, loading/error states without custom code |
| Icons | `lucide-react` | 1.75.0 | Tree-shakeable, consistent stroke weights |
| API | `fastapi` | 0.164.0 | Async, OpenAPI-first, dependency injection |
| Validation/models | `pydantic` | 2.14.3 | Same schema drives validation + OpenAPI + JSON schema for Gemini |
| ORM | `sqlalchemy` | 2.1.9 (async) | Typed 2.0 style, no N+1 by default |
| Driver | `psycopg[binary]` | 3.3.9 | Async Postgres driver |
| Migrations | `alembic` | 1.20.1 | Versioned schema |
| Server | `uvicorn` | 0.54.0 | ASGI, single worker on small instances |
| HTTP client | `httpx` | 0.28.1 | Async, timeouts, connection limits |
| Settings | `pydantic-settings` | 2.16.3 | Env validation at boot; fail fast |
| Logging | `structlog` | 26.1.0 | JSON logs with redaction |
| Resilience | `tenacity` | 9.2.1 | Bounded retries with jitter |
| Rate limiting | `limits` | 5.8.0 | In-process sliding window |
| LLM | `google-genai` | 3.5.0 | Official SDK |
| DB | PostgreSQL | 17 | JSONB, partial indexes, `gen_random_uuid()` |
| Tests BE | `pytest` 9.2.0, `pytest-asyncio` 1.5.0, `pytest-cov` 7.1.0, `respx` 0.23.1, `hypothesis` 6.170.15 | | |
| Tests FE | `vitest` 5.1.1, `@testing-library/react` 16.3.3, `jsdom`, `@playwright/test` 1.65.1, `@axe-core/playwright` 4.14.0 | | |
| Lint/format | `eslint` 10.15.0, `prettier` 3.10.1, `ruff` 0.17.5, `black` 26.10.1, `mypy` 2.4.1, `bandit` 1.9.4 | | |
| Contracts | `openapi-typescript` 7.13.0 | Generate TS types from FastAPI's OpenAPI schema; CI fails on drift |

Formatting policy: **Black formats, Ruff lints** (`ruff-format` disabled to avoid two formatters);
`E501` disabled because Black owns line length. MyPy in `strict` mode for `domain/`, `services/`,
`providers/`; `--check-untyped-defs` elsewhere.

### 3.2 Supporting libraries — justification

`@tanstack/react-query` and `openapi-typescript` are additions to the stated stack. They replace
more code than they add: query caching/retry/abort (≈200 LOC saved per feature) and a
compile-time contract against the backend (prevents an entire class of integration bugs).
No state-management library is added; server state is the only state.

---

## 4. System architecture

### 4.1 Container view

```mermaid
flowchart LR
    U[Browser] -->|HTTPS| W[Next.js 16 on Vercel]
    W -->|REST + Bearer| A[FastAPI on Render]
    A -->|SQL| P[(PostgreSQL 17)]
    A -->|HTTPS| OM[Open-Meteo Air Quality + Geocoding]
    A -.->|optional| OA[OpenAQ v3]
    A -.->|optional, off| CG[data.gov.in CPCB]
    A -.->|optional| OSRM[OSRM demo]
    A -->|HTTPS| G[Gemini API]
    W -->|tiles| T[OpenStreetMap]
```

No Redis, no queue, no worker, no microservice. Forecasts are fetched on demand and cached in
Postgres. This is the right size for the load; adding infrastructure would add failure modes
without adding user value.

### 4.2 Backend layers and dependency rules

```
api/v1/*.py         HTTP only: parse, authorise, delegate, serialise. No business logic.
   ↓
services/*.py       Orchestration + transactions. May call domain, repositories, providers.
   ↓
domain/*.py         PURE functions. stdlib + math only. No I/O, no ORM, no HTTP, no clock.
   ↓
repositories/*.py   SQLAlchemy queries only. Return models/DTOs. No business rules.
providers/*.py      External I/O behind Protocol interfaces. Normalise to internal DTOs.
```

Enforced rules:
- `domain/` is imported by nothing below it and imports nothing from the app (verified by an
  import-linter test in CI).
- Routers never touch `AsyncSession` directly; only services do.
- Providers never raise raw `httpx` exceptions upward; they return `ProviderResult` or raise the
  domain error taxonomy (§12).
- ORM models never leak into API schemas; Pydantic response models are explicit.

### 4.3 Frontend layers

```
app/            Route segments + layouts only (composition, metadata, error boundaries)
features/<x>/   components, hooks, api client, zod schemas, local types
components/ui   shadcn primitives (owned)
lib/            api client, problem-details parser, session, formatting, aqi labels
```

Rules: no `fetch` outside `lib/api`; no business arithmetic in components (AQI labels and
formatting are presentation helpers, the AQI *value* comes from the API); every chart has a
sibling `<table>`; Leaflet and Recharts are dynamically imported with `ssr: false`.

### 4.4 Request lifecycle (read path)

1. Client sends `GET /v1/air/current?lat&lon` with `Authorization: Bearer <opaque>` (optional).
2. API validates ranges, **rounds coordinates to 2 decimals** (~1.1 km) — privacy *and* cache hit.
3. `AirService` checks in-process LRU (60 s) → Postgres snapshot cache (30 min) → provider.
4. Provider adapter calls Open-Meteo with 5 s connect / 8 s total timeout, circuit breaker,
   `httpx` connection pool limits.
5. Response normalised to `AirQualityReading` (values may be `None`), CPCB AQI computed in
   `domain/aqi.py`, provenance assembled.
6. Snapshot + fetch log persisted (async, non-blocking on failure).
7. Response wrapped in `{data, meta}` with `attribution`, `age_minutes`, `stale`, `request_id`.

### 4.5 Module map (7 required modules → code)

| Module | Frontend route | Backend service | Pure domain |
|---|---|---|---|
| 1 Air Intelligence | `/air` | `AirService` | `aqi.py`, `trends.py` |
| 2 Family Intelligence | `/family` | `HouseholdService` | `risk.py` |
| 3 SmartRoutine AI | `/routine` | `RoutineService` | `routine_engine.py`, `dose.py` |
| 4 IndoorShield AI | `/indoor` | `IndoorService` | `indoor_model.py` |
| 5 EcoRoute AI | `/ecoroute` | `EcoRouteService` | `carbon.py`, `dose.py` |
| 6 Impact Intelligence | `/impact` | `ImpactService` | `carbon.py`, `factors.py` |
| 7 SAANS AI Copilot | `/copilot` | `CopilotService` | `factpack.py`, `validators.py` |

---

## 5. Repository structure

```
saans-saathi-ai/
├─ .github/
│  ├─ workflows/ci.yml
│  └─ dependabot.yml
├─ apps/
│  ├─ api/
│  │  ├─ app/
│  │  │  ├─ main.py
│  │  │  ├─ core/            config, logging, errors, security, rate_limit, middleware, deps
│  │  │  ├─ api/v1/          router + one module per resource
│  │  │  ├─ schemas/         pydantic request/response models
│  │  │  ├─ models/          SQLAlchemy models
│  │  │  ├─ repositories/    SQL access
│  │  │  ├─ services/        orchestration
│  │  │  ├─ domain/          PURE functions (aqi, dose, carbon, indoor, routine, risk)
│  │  │  ├─ providers/       open_meteo, openaq, cpcb, routing, cache, circuit_breaker
│  │  │  ├─ factors/         versioned JSON factor registry + provenance
│  │  │  └─ db/              session, alembic/
│  │  ├─ tests/              unit/, integration/, contract/, ai/
│  │  ├─ pyproject.toml
│  │  ├─ Dockerfile
│  │  └─ alembic.ini
│  └─ web/
│     ├─ src/
│     │  ├─ app/             (app)/air, family, routine, indoor, ecoroute, impact, copilot
│     │  ├─ components/ui/
│     │  ├─ features/        air, family, routine, indoor, ecoroute, impact, copilot
│     │  ├─ lib/             api/, aqi.ts, format.ts, session.ts
│     │  └─ messages/en.ts
│     ├─ public/             logo, og image (<200 KB each)
│     ├─ package.json
│     ├─ next.config.ts
│     ├─ tailwind.config.ts  (v4 CSS-first via globals.css)
│     └─ vitest.config.ts
├─ docs/
│  ├─ BLUEPRINT.md           (this file)
│  ├─ ARCHITECTURE.md        (short public version)
│  └─ FACTORS.md             (human-readable emission-factor methodology)
├─ scripts/
│  ├─ check_repo_size.sh
│  ├─ check_single_branch.sh
│  └─ verify_factors.py      (asserts every factor has source_url + version)
├─ docker-compose.yml        (local Postgres 17 only)
├─ .env.example
├─ .gitignore
├─ .pre-commit-config.yaml   (optional, mirrors CI)
├─ LICENSE
└─ README.md
```

Repo constraints: one branch (`main`), no `develop`; no build artefacts, no `node_modules`,
no `.venv`, no Playwright reports, no datasets. CI enforces < 10 MB (tracked files) and exactly
one remote branch.

---

## 6. Database design

### 6.1 Entity relationship diagram

```mermaid
erDiagram
    PROFILES ||--o| HOUSEHOLDS : "owns (0..1)"
    HOUSEHOLDS ||--o{ HOUSEHOLD_MEMBERS : has
    HOUSEHOLDS ||--|| HOUSEHOLD_PREFERENCES : configures
    HOUSEHOLDS ||--o{ SAVED_LOCATIONS : saves
    HOUSEHOLDS ||--o{ ROUTINES : generates
    HOUSEHOLDS ||--o{ RECOMMENDATIONS : receives
    HOUSEHOLDS ||--o{ SUSTAINABILITY_ACTIVITIES : logs
    PROFILES ||--o{ AI_CONVERSATIONS : starts
    AI_CONVERSATIONS ||--o{ AI_MESSAGES : contains
    AIR_QUALITY_FETCHES ||--o{ AIR_QUALITY_SNAPSHOTS : produces
    ROUTINES ||--o{ RECOMMENDATIONS : yields
```

Notes: `PROFILES` is an anonymous device identity, not a person. There is deliberately **no**
email, phone, name, or password column. Health flags live in `HOUSEHOLD_MEMBERS` behind an explicit
consent timestamp and are never sent to third parties.

### 6.2 Core DDL

```sql
CREATE TABLE profiles (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  token_hash       bytea NOT NULL UNIQUE,           -- sha256(opaque 256-bit token)
  consent_version  text  NOT NULL,
  health_consent_at timestamptz,                    -- non-null required before health flags
  created_at       timestamptz NOT NULL DEFAULT now(),
  last_seen_at     timestamptz NOT NULL DEFAULT now(),
  expires_at       timestamptz NOT NULL,
  deleted_at       timestamptz
);

CREATE TABLE households (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id     uuid NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
  lat            numeric(6,3) CHECK (lat BETWEEN -90 AND 90),   -- stored rounded to 3 dp
  lon            numeric(6,3) CHECK (lon BETWEEN -180 AND 180),
  city           text,
  timezone       text NOT NULL DEFAULT 'Asia/Kolkata',
  dwelling       text NOT NULL CHECK (dwelling IN
                   ('apartment_ground','apartment_upper','independent','other')),
  cooking_fuel   text NOT NULL CHECK (cooking_fuel IN
                   ('lpg','png','induction','biomass','mixed','other')),
  has_purifier   boolean NOT NULL DEFAULT false,
  purifier_cadr  integer CHECK (purifier_cadr BETWEEN 50 AND 1500),   -- m3/h
  room_area_m2   integer CHECK (room_area_m2 BETWEEN 5 AND 300),
  ceiling_m      numeric(3,2) CHECK (ceiling_m BETWEEN 2.0 AND 5.0),
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE household_members (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id  uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
  age_band      text NOT NULL CHECK (age_band IN
                  ('0-5','6-12','13-17','18-59','60+')),
  health_flags  text[] NOT NULL DEFAULT '{}'
                  CHECK (health_flags <@ ARRAY['asthma','copd','heart','pregnant','none']),
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_members_household ON household_members(household_id);

CREATE TABLE air_quality_snapshots (
  id           bigserial PRIMARY KEY,
  provider     text NOT NULL,
  lat_key      numeric(5,2) NOT NULL,      -- 2 dp ≈ 1.1 km
  lon_key      numeric(5,2) NOT NULL,
  kind         text NOT NULL CHECK (kind IN ('modelled','measured')),
  observed_at  timestamptz NOT NULL,
  fetched_at   timestamptz NOT NULL DEFAULT now(),
  expires_at   timestamptz NOT NULL,
  pm2_5        real, pm10 real, co_ug_m3 real,
  no2_ug_m3    real, so2_ug_m3 real, o3_ug_m3 real, dust_ug_m3 real,
  us_aqi       smallint, eu_aqi smallint,
  station_id   text, station_distance_km real,
  raw          jsonb,
  UNIQUE (provider, lat_key, lon_key, observed_at)
);
CREATE INDEX ix_snap_lookup ON air_quality_snapshots (lat_key, lon_key, observed_at DESC);

CREATE TABLE air_quality_forecasts (
  id          bigserial PRIMARY KEY,
  provider    text NOT NULL,
  lat_key     numeric(5,2) NOT NULL,
  lon_key     numeric(5,2) NOT NULL,
  issued_at   timestamptz NOT NULL,
  series      jsonb NOT NULL,   -- hourly points, schema-validated by Pydantic
  expires_at  timestamptz NOT NULL,
  UNIQUE (provider, lat_key, lon_key, issued_at)
);

CREATE TABLE air_quality_fetch_log (
  id          bigserial PRIMARY KEY,
  provider    text NOT NULL,
  status      text NOT NULL CHECK (status IN ('ok','timeout','http_error','parse_error','circuit_open')),
  http_status smallint,
  latency_ms  integer,
  lat_key     numeric(5,2),
  lon_key     numeric(5,2),
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_fetch_log_created ON air_quality_fetch_log (created_at DESC);

CREATE TABLE routines (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id   uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
  plan_date      date NOT NULL,
  timezone       text NOT NULL,
  engine_version text NOT NULL,
  inputs_hash    text NOT NULL,
  plan           jsonb NOT NULL,
  generated_at   timestamptz NOT NULL DEFAULT now(),
  expires_at     timestamptz NOT NULL,
  UNIQUE (household_id, plan_date, inputs_hash)
);
CREATE INDEX ix_routines_household_date ON routines (household_id, plan_date DESC);

CREATE TABLE recommendations (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
  routine_id   uuid REFERENCES routines(id) ON DELETE SET NULL,
  module       text NOT NULL CHECK (module IN
                 ('air','family','routine','indoor','ecoroute','impact','copilot')),
  severity     text NOT NULL CHECK (severity IN
                 ('good','satisfactory','moderate','poor','very_poor','severe','info')),
  title        text NOT NULL,
  body         text NOT NULL,
  fact_refs    jsonb NOT NULL DEFAULT '[]',
  source       text NOT NULL CHECK (source IN ('deterministic','ai')),
  model        text,
  valid_until  timestamptz,
  dismissed_at timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_recs_household_created ON recommendations (household_id, created_at DESC);

CREATE TABLE sustainability_activities (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id     uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
  activity_type    text NOT NULL,
  occurred_on      date NOT NULL,
  quantity         numeric(10,3) NOT NULL CHECK (quantity >= 0),
  unit             text NOT NULL,
  co2e_kg          numeric(10,4) NOT NULL,
  factor_key       text NOT NULL,
  factor_value     numeric(12,6) NOT NULL,
  factor_unit      text NOT NULL,
  factor_version   text NOT NULL,
  factor_source_url text NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_activities_household_date ON sustainability_activities (household_id, occurred_on DESC);

CREATE TABLE ai_conversations (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id     uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  context_lat_key numeric(5,2),
  context_lon_key numeric(5,2),
  created_at     timestamptz NOT NULL DEFAULT now(),
  last_message_at timestamptz NOT NULL DEFAULT now(),
  expires_at     timestamptz NOT NULL
);

CREATE TABLE ai_messages (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES ai_conversations(id) ON DELETE CASCADE,
  role            text NOT NULL CHECK (role IN ('user','assistant')),
  content         text NOT NULL,
  structured      jsonb,
  fact_pack_hash  text,
  model           text,
  input_tokens    integer,
  output_tokens   integer,
  latency_ms      integer,
  validation      text CHECK (validation IN ('valid','rejected','fallback')),
  error_code      text,
  created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_ai_messages_conv ON ai_messages (conversation_id, created_at);

-- Daily quota/budget counters for any metered dependency (key = 'gemini' | 'openmeteo' | ...).
CREATE TABLE usage_daily (
  day           date    NOT NULL,
  key           text    NOT NULL,
  requests      integer NOT NULL DEFAULT 0,
  input_tokens  bigint  NOT NULL DEFAULT 0,
  output_tokens bigint  NOT NULL DEFAULT 0,
  PRIMARY KEY (day, key)
);

CREATE TABLE privacy_events (
  id         bigserial PRIMARY KEY,
  profile_id uuid REFERENCES profiles(id) ON DELETE SET NULL,
  event      text NOT NULL CHECK (event IN ('consent','delete_all','data_export')),
  meta       jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);
```

### 6.3 Relationships and integrity

| Relationship | Cardinality | Delete rule | Why |
|---|---|---|---|
| profile → household | 1 : 0..1 | CASCADE | A device may browse before creating a household |
| household → members | 1 : 0..6 | CASCADE | Household context |
| household → preferences | 1 : 1 | CASCADE | Split so preferences can change without rewriting the household |
| household → routines | 1 : N | CASCADE | Idempotent per (date, inputs_hash) |
| profile → conversations | 1 : N | CASCADE | Deletion must remove chat history |
| routine → recommendations | 1 : N | SET NULL | Advice can outlive a plan |

### 6.4 Indexes and query patterns

- Air lookups are always `(lat_key, lon_key, observed_at DESC)`; unique constraint doubles as the
  cache identity and prevents duplicate rows.
- `routines` unique `(household_id, plan_date, inputs_hash)` makes generation idempotent — repeated
  taps return the stored plan (cheap, and prevents double Gemini spend).
- All personal-data queries are bounded by `household_id` and ordered by time; partial indexes are
  unnecessary at this scale.
- JSONB holds only server-generated, schema-validated payloads (plan, forecast series, fact refs).

### 6.5 Retention and deletion

| Data | Retention | Mechanism |
|---|---|---|
| Air snapshots / forecasts | 90 days / 7 days | Nightly `DELETE` in a startup-maintenance task (single instance) |
| Fetch logs | 30 days | Same job |
| Routines / recommendations | 90 / 30 days | Same job |
| AI conversations and messages | 30 days | Same job + user-initiated delete |
| Profile, household, activities | Until user deletes | `DELETE /v1/session` hard-deletes the profile; FK cascades remove everything |
| Privacy events | 12 months | No message content, only event type |

`DELETE /v1/session` performs the deletion synchronously and returns `204`; the UI confirms with an
explicit second action. No soft-delete of personal content.

### 6.6 Privacy by design (mapped to India's DPDP Act 2023 principles)

- **Data minimisation:** no name, email, phone, gender, exact address, or free-text notes.
- **Purpose limitation:** health flags are optional and used only for risk classification.
- **Location precision:** stored at 3 dp (≈110 m), *sent to providers* at 2 dp (≈1.1 km).
- **Consent:** `consent_version` on the profile; `health_consent_at` required before any health flag
  is accepted (API returns `CONSENT_REQUIRED` otherwise).
- **Erasure:** one endpoint, cascading, immediate.
- **Third-party disclosure:** the consent screen names Open-Meteo, OpenAQ (if enabled) and Google
  Gemini, and states what is shared (rounded coordinates, ages bands, no identifiers).
- Legal review of the consent copy is out of scope for the hackathon and is recorded as a risk.

---

## 7. API design

### 7.1 Global contract

- Base: `https://<render-service>/v1`, JSON UTF-8 only. Operational endpoints (`/healthz`,
  `/readyz`) live at the service root, outside `/v1`.
- Success: `{ "data": <resource|array>, "meta": { "request_id", "generated_at", ... } }`.
- Lists: `data` is an array; `meta.pagination = { next_cursor, has_more }`.
- Errors: `application/problem+json` (RFC 9457) with `type`, `title`, `status`, `detail`,
  `instance`, `code`, `request_id`, optional `retry_after`, optional `errors[]` for field errors.
- Auth: `Authorization: Bearer <opaque 256-bit token>`; token returned exactly once by
  `POST /v1/sessions`, stored client-side, sent only over HTTPS.
- Idempotency: `POST /v1/routines` is idempotent by `(household, date, inputs_hash)`.
- CORS: exact allowlist via `ALLOWED_ORIGINS`; no wildcard; `Vary: Origin`.
- Limits: 32 KB body, 100 req/min/session, 30 req/min/IP for public air reads, 20 AI messages/hour.
- Headers: `X-Request-ID` echoed; `Cache-Control: private, max-age=0` for personal data,
  `public, max-age=300` + `ETag` for public air reads.

### 7.2 Endpoint catalogue

| # | Method | Route | Auth | Purpose | Request | Response `data` | Key errors |
|---|---|---|---|---|---|---|---|
| 1 | POST | `/sessions` | — | Create anonymous session | `{consent_version, health_consent: bool}` | `{token, expires_at, profile_id}` | 400, 429 |
| 2 | GET | `/session` | Session | Session + onboarding state | — | `{profile_id, has_household, consent}` | 401 |
| 3 | DELETE | `/session` | Session | Erase all personal data | — | `204` | 401 |
| 4 | GET | `/geo/search` | Public | Place search | `?q&limit=1..8&country=IN` | `Place[]` | 400, 429, 503 |
| 5 | GET | `/air/current` | Public | Current reading + CPCB AQI | `?lat&lon` | `AirCurrent` | 400, 422, 429, 503 |
| 6 | GET | `/air/forecast` | Public | Hourly forecast + windows | `?lat&lon&hours=24\|48\|72` | `AirForecast` | 400, 422, 503 |
| 7 | GET | `/air/history` | Public | Daily aggregates | `?lat&lon&days=1..90` | `AirHistory` | 400, 422, 503 |
| 8 | GET | `/household` | Session | Read household | — | `Household` | 401, 404 |
| 9 | PUT | `/household` | Session | Upsert household | `HouseholdUpsert` | `Household` | 400, 401, 422 |
| 10 | GET | `/household/members` | Session | List members | — | `Member[]` | 401 |
| 11 | POST | `/household/members` | Session | Add member | `{age_band, health_flags}` | `Member` | 401, 403 (`CONSENT_REQUIRED`), 422 |
| 12 | PATCH | `/household/members/{id}` | Session | Update member | partial | `Member` | 401, 403, 404, 422 |
| 13 | DELETE | `/household/members/{id}` | Session | Remove member | — | `204` | 401, 404 |
| 14 | GET | `/household/preferences` | Session | Read preferences | — | `Preferences` | 401, 404 |
| 15 | PUT | `/household/preferences` | Session | Update preferences | `Preferences` | `Preferences` | 401, 422 |
| 16 | GET | `/locations` | Session | Saved locations | — | `SavedLocation[]` | 401 |
| 17 | POST | `/locations` | Session | Save location | `{label, kind, lat, lon}` | `SavedLocation` | 401, 409, 422 |
| 18 | DELETE | `/locations/{id}` | Session | Delete location | — | `204` | 401, 404 |
| 19 | POST | `/routines` | Session | Generate plan (idempotent) | `{date, horizon_days:0..6, refresh?:bool}` | `RoutinePlan` | 401, 422, 503 |
| 20 | GET | `/routines/{date}` | Session | Read plan | — | `RoutinePlan` | 401, 404 |
| 21 | PATCH | `/routines/items/{item_id}` | Session | Mark item done/skipped | `{status}` | `RoutinePlan` | 401, 404, 422 |
| 22 | POST | `/indoor/assessment` | Session | Indoor estimate + actions | `{location?:{lat,lon}, overrides?}` | `IndoorAssessment` | 401, 422, 503 |
| 23 | POST | `/ecoroute/compare` | Session | Mode comparison | `{origin, destination, depart_at?, modes[]}` | `EcoRouteComparison` | 400, 401, 422, 503 |
| 24 | POST | `/impact/activities` | Session | Log activity | `{activity_type, quantity, unit, occurred_on}` | `Activity` | 401, 422 |
| 25 | GET | `/impact/activities` | Session | List activities | `?from&to&limit` | `Activity[]` | 401, 422 |
| 26 | DELETE | `/impact/activities/{id}` | Session | Delete activity | — | `204` | 401, 404 |
| 27 | GET | `/impact/summary` | Session | Totals + breakdown | `?range=7d\|30d\|90d` | `ImpactSummary` | 401, 422 |
| 28 | GET | `/impact/factors` | Public | Factor registry | — | `Factor[]` | 503 |
| 29 | POST | `/copilot/chat` | Session | Grounded answer | `{message, conversation_id?, context?}` | `CopilotAnswer` | 401, 422, 429, 503 |
| 30 | GET | `/copilot/conversations/{id}` | Session | History | `?limit` | `Message[]` | 401, 404 |
| 31 | DELETE | `/copilot/conversations/{id}` | Session | Delete conversation | — | `204` | 401, 404 |
| 32 | GET | `/healthz` | Public | Liveness (no DB) | — | `{status}` | — |
| 33 | GET | `/readyz` | Public | DB + cache readiness | — | `{status, checks}` | 503 |
| 34 | GET | `/meta` | Public | Version, model, data sources | — | `Meta` | — |

### 7.3 Representative payloads

**`GET /v1/air/current?lat=28.6139&lon=77.2090` → 200**

```json
{
  "data": {
    "location": {
      "requested": { "lat": 28.6139, "lon": 77.209 },
      "resolved":  { "lat": 28.599998, "lon": 77.20001 },
      "timezone": "Asia/Kolkata"
    },
    "reading": {
      "pm2_5": 75.2, "pm10": 76.4, "co_ug_m3": 1581.0,
      "no2_ug_m3": 63.7, "so2_ug_m3": 27.9, "o3_ug_m3": 26.0,
      "dust_ug_m3": null
    },
    "cpcb_aqi": {
      "value": 151, "category": "moderate", "dominant_pollutant": "pm2_5",
      "method": "CPCB-2014", "coverage": ["pm2_5","pm10","no2","so2","o3","co"],
      "partial": false
    },
    "provider_aqi": { "us": 166, "european": 73, "note": "Different scales; not comparable to CPCB AQI" },
    "provenance": {
      "provider": "open-meteo", "kind": "modelled", "model": "CAMS ENSEMBLE",
      "observed_at": "2026-11-18T17:00:00Z", "fetched_at": "2026-11-18T17:02:11Z",
      "age_minutes": 2, "stale": false,
      "attribution": ["CAMS ENSEMBLE (Copernicus)", "Open-Meteo.com"]
    }
  },
  "meta": { "request_id": "01J...", "generated_at": "2026-11-18T17:02:11Z", "cache": { "hit": false, "expires_at": "2026-11-18T17:32:11Z" } }
}
```

**`POST /v1/routines` → 200** (fields abbreviated)

```json
{
  "data": {
    "id": "…", "date": "2026-11-19", "timezone": "Asia/Kolkata",
    "engine_version": "routine-1.0.0", "confidence": "medium",
    "blocks": [
      {
        "id": "b1", "title": "Morning walk", "start": "06:30", "end": "07:00",
        "activity": "walk", "intensity": "moderate", "venue": "outdoor",
        "status": "recommended",
        "exposure": { "dose_ug": 96.4, "index": 42 },
        "rationale": [{ "template_id": "routine.lowest_forecast_window",
                        "params": { "pm2_5": 48.2, "hour": 6 } }],
        "fact_refs": ["aq.forecast.min_pm2_5", "aq.forecast.best_window_06_10"]
      }
    ],
    "alternatives": [{ "block_id": "b1", "start": "18:00", "status": "avoid",
                       "rationale": [{ "template_id": "routine.high_evening_pm" }] }],
    "data_quality": { "forecast_provider": "open-meteo", "stale": false }
  },
  "meta": { "request_id": "…", "generated_at": "…" }
}
```

**`POST /v1/ecoroute/compare` → 200** (abbreviated)

```json
{
  "data": {
    "route": { "distance_km": 8.4, "duration_min": 26, "source": "osrm", "is_estimate": true },
    "modes": [
      { "mode": "metro",  "co2e_kg": 0.21, "exposure_index": 28, "duration_min": 31,
        "recommended_for": ["carbon","air"] },
      { "mode": "car",    "co2e_kg": 1.36, "exposure_index": 100, "duration_min": 22,
        "recommended_for": [] },
      { "mode": "cycle",  "co2e_kg": 0.0,  "exposure_index": 165, "duration_min": 34,
        "recommended_for": ["carbon"] }
    ],
    "tradeoff_note": "Cycling is lowest-carbon but highest inhaled dose today; metro is lowest on both.",
    "assumptions": [{ "key": "car_petrol_l_per_100km", "value": 7.0, "source": "user_default" }]
  },
  "meta": { "request_id": "…" }
}
```

**`POST /v1/copilot/chat` → 200**

```json
{
  "data": {
    "conversation_id": "…", "message_id": "…",
    "answer": "Outdoor PM2.5 peaks near 19:00. Move the walk to 06:30–07:00 and keep windows closed after 18:00.",
    "severity": "moderate",
    "actions": [
      { "title": "Walk at 06:30", "detail": "Forecast PM2.5 is lowest then.",
        "time_window": "06:30-07:00", "fact_refs": ["aq.forecast.min_pm2_5"], "confidence": "high" }
    ],
    "avoid": [{ "title": "Outdoor exercise after 18:00", "reason_fact_ref": "aq.forecast.max_pm2_5" }],
    "citations": [
      { "fact_id": "aq.forecast.min_pm2_5", "label": "Lowest forecast PM2.5",
        "value": 48.2, "unit": "µg/m³", "source": "Open-Meteo (CAMS)", "observed_at": "2026-11-19T06:00:00Z" }
    ],
    "source": "ai", "model": "gemini-3.5-flash-lite", "latency_ms": 1840,
    "disclaimer": "General guidance, not medical advice."
  },
  "meta": { "request_id": "…" }
}
```

### 7.4 Validation rules

| Field | Rule | Error |
|---|---|---|
| `lat` / `lon` | finite number, `-90..90` / `-180..180`; rejected if outside | 422 `LOCATION_INVALID` |
| `q` | 1–80 chars after trim; no control chars, no URLs | 422 `SEARCH_QUERY_INVALID` |
| `message` | 1–800 chars; control chars stripped; refused if it contains > 4 URLs | 422 `MESSAGE_INVALID` |
| `hours` | ∈ {24,48,72} | 422 |
| `days` | 1–90 | 422 |
| `date` | ISO date, within today..today+6 (household TZ) | 422 `DATE_OUT_OF_RANGE` |
| `mode` | enum | 422 |
| `age_band` / `health_flags` | enum / subset | 422 |
| `quantity` | 0 < q ≤ 100000 | 422 |
| Body size | ≤ 32 KB | 413 |
| Unknown fields | rejected (`model_config = ConfigDict(extra="forbid")`) | 422 |

---

## 8. AI integration architecture (SAANS AI Copilot)

### 8.1 Operating principle

Gemini is a **renderer of verified facts**, never a source of them. The engine produces a
`FactPack`; Gemini must return a schema whose every action cites a `fact_id` from that pack.
Anything else is rejected and replaced by the deterministic composer.

### 8.2 FactPack (server-built, trusted input)

```json
{
  "facts": [
    { "id": "aq.current.pm2_5", "label": "PM2.5 now", "value": 75.2, "unit": "µg/m³",
      "source": "Open-Meteo (CAMS)", "observed_at": "2026-11-18T17:00:00Z", "kind": "modelled" },
    { "id": "aq.current.aqi_cpcb", "label": "CPCB AQI now", "value": 151, "unit": "index",
      "category": "moderate", "source": "computed", "observed_at": "2026-11-18T17:00:00Z" },
    { "id": "aq.forecast.min_pm2_5", "label": "Lowest forecast PM2.5 (next 24 h)", "value": 48.2,
      "unit": "µg/m³", "at": "2026-11-19T06:00:00Z", "source": "Open-Meteo (CAMS)" },
    { "id": "aq.forecast.max_pm2_5", "label": "Highest forecast PM2.5 (next 24 h)", "value": 118.6,
      "unit": "µg/m³", "at": "2026-11-19T20:00:00Z", "source": "Open-Meteo (CAMS)" }
  ],
  "context": {
    "city": "New Delhi", "timezone": "Asia/Kolkata",
    "sensitive_group": true, "has_children": true, "has_purifier": false, "cooking_fuel": "png"
  },
  "engine": {
    "risk_level": "moderate",
    "best_window": { "start": "06:30", "end": "07:00", "pm2_5": 48.2 },
    "worst_window": { "start": "19:00", "end": "21:00", "pm2_5": 118.6 }
  }
}
```

Rules: ≤ 40 facts, ≤ 1,200 tokens, **no names, no free text from the user, no exact coordinates,
no health labels** — only derived booleans (`sensitive_group`, `has_children`). Anything not needed
for phrasing is excluded.

### 8.3 Prompt structure (trust boundary)

- **System instruction (trusted):** role, hard rules ("use only facts; cite `fact_id`; never give
  medical advice; never output URLs, HTML or markdown links; max 5 actions; if the facts do not
  answer the question, say so"), and the FactPack JSON.
- **User turn (untrusted):** the user message only, wrapped as data. It never reaches the system
  instruction. The model is instructed to treat it as a question, not as instructions.

Because the response schema has no free-text URL or code field and the model has **no tools**,
prompt injection cannot cause actions, data exfiltration, or extra API calls. The worst case is a
useless answer, which the validator catches.

### 8.4 Output schema (also enforced by Gemini)

```json
{
  "answer": "string, <= 600 chars",
  "actions": [{
    "title": "string, <= 60 chars",
    "detail": "string, <= 160 chars",
    "time_window": "HH:MM-HH:MM | null",
    "fact_refs": ["aq.current.pm2_5"],
    "confidence": "high | medium | low"
  }],
  "avoid": [{ "title": "string", "reason_fact_ref": "aq.forecast.max_pm2_5" }]
}
```

Gemini ignores `minLength`/`maxLength` during constrained decoding, so **all limits are re-checked
in Pydantic**.

### 8.5 Post-validation pipeline (fail-closed)

| # | Check | On failure |
|---|---|---|
| 1 | Valid JSON | fallback |
| 2 | Pydantic strict validation (`extra="forbid"`) | fallback |
| 3 | ≤ 5 actions, lengths within limits | truncate to 5, then validate |
| 4 | Every `fact_ref` exists in the pack | fallback |
| 5 | Every numeric token in output matches a pack value (±1%) or is an allowlisted small integer (0–24, times, "2 hours") | fallback (strict mode) |
| 6 | No URL, HTML tag, or code fence; no medical claim verbs (diagnose/cure/dosage/prescribe) | strip line; if body becomes empty → fallback |
| 7 | Citations are built **server-side** from the pack, never copied from the model | — |

Validation outcomes are logged as `validation: valid | rejected | fallback`. A rejected response is
never shown to the user.

### 8.6 Fallback composer (deterministic, same schema)

Templates keyed by `(risk_level, best_window exists?, household flags)` produce a 2–3 sentence
answer plus 1–3 actions with the same citation shape. The UI labels it "Guidance (offline mode) —
AI unavailable" so the degradation is visible, not hidden.

Triggers: missing/invalid `GEMINI_API_KEY`, quota exhausted, 5xx after one retry, timeout > 12 s,
validation rejection, daily budget reached.

### 8.7 Token, cost and quota control

- Request budget: system+facts ≤ 1,200 tokens, history ≤ 600 tokens (last 4 turns, truncated),
  output ≤ 350 tokens → ≈ 2,150 tokens per call.
- Cost at `gemini-3.5-flash-lite` ($0.30 / $2.50 per 1M): ≈ **$0.0015 per answer**. At 300 answers/day
  that is ≈ $0.45/day. Prices rise 2026-12-01 — the model ID and budget are configuration.
- Hard server budget: `AI_DAILY_REQUEST_BUDGET` (default 300) enforced atomically:

```sql
INSERT INTO usage_daily (day, key, requests) VALUES (CURRENT_DATE, 'gemini', 1)
ON CONFLICT (day, key) DO UPDATE SET requests = usage_daily.requests + 1
WHERE usage_daily.requests < :budget
RETURNING requests;
```
  No row returned → skip the API call, serve the deterministic answer (do **not** error the user).
- Per-session: 20 messages/hour; per-IP unauthenticated: 0 (copilot requires a session).
- Response cache: in-process, keyed by `sha256(factpack + normalized message + locale)`, TTL 15 min.

### 8.8 Gemini client adapter

- One module, `providers/gemini.py`; the SDK call is isolated so a future API-shape change
  (`generate_content` vs `interactions.create`) touches one file.
- `google-genai` 3.5.0 is used via `client.models.generate_content` with
  `types.GenerateContentConfig(response_mime_type="application/json",
  response_json_schema=<pydantic schema>, temperature=0.2, max_output_tokens=350)`.
- Startup smoke test is **not** automatic (costs quota). A CI job runs `tests/ai/test_smoke.py`
  only when `GEMINI_API_KEY` is present; otherwise it is skipped with an explicit reason.

### 8.9 Conversation history

Last 4 turns are retrieved by `conversation_id` scoped to the profile. History is included only as
`role: user` short text (≤ 400 chars each) with numbers stripped, so stale numbers cannot leak into
a new answer. Facts are always rebuilt fresh.

---

## 9. Data-provider architecture

### 9.1 Interface

```python
class AirQualityProvider(Protocol):
    name: str
    async def current(self, lat: float, lon: float) -> ProviderReading: ...
    async def forecast(self, lat: float, lon: float, hours: int) -> ProviderForecast: ...
    async def history(self, lat: float, lon: float, days: int) -> ProviderHistory: ...

@dataclass(frozen=True)
class ProviderReading:
    values: dict[Pollutant, float | None]      # missing pollutants are None, never 0
    observed_at: datetime                       # UTC
    kind: Literal["modelled", "measured"]
    provider: str
    station_id: str | None
    station_distance_km: float | None
    attribution: tuple[str, ...]
    quality_flags: tuple[str, ...]
```

### 9.2 Resolution chain (per request)

```
in-process LRU (60 s)
  → Postgres snapshot (TTL 30 min current / 3 h forecast / 24 h history)
    → live provider (retry ≤ 2, 5 s connect / 8 s total, circuit breaker)
      → stale Postgres row ≤ 24 h  ⟶ 200 with stale=true + age_minutes
        → 503 PROVIDER_UNAVAILABLE (no data, no invention)
```

The stale step is deliberate: a 6-hour-old modelled forecast is still decision-relevant **if
labelled**. Beyond 24 h it is deleted from consideration.

### 9.3 Circuit breaker

Per provider, in-process: 5 consecutive failures (or 3 timeouts in 60 s) → open for 60 s →
one half-open probe. State is exposed on `/v1/meta` for debugging. With one API instance this is
sufficient; no distributed breaker is warranted.

### 9.4 Caching policy

| Data | Key | TTL | Rationale |
|---|---|---|---|
| Current reading | `(provider, lat2, lon2)` | 30 min | Upstream updates every 12–24 h; 30 min keeps "fresh" honest and stays far under 10k/day |
| Forecast | `(provider, lat2, lon2, day)` | 3 h | Forecast changes only on model runs |
| History | `(provider, lat2, lon2, day)` | 24 h | Immutable past |
| Geocoding | normalised query | 24 h | Place names change rarely |

Worst case at 500 unique locations: 500 × 48 = 24,000 fetches/day — **above** the 10k free limit.
Therefore: a global upstream budget (`OPENMETEO_DAILY_CALL_BUDGET`, default 8,000) is tracked in
`usage_daily` under `key='openmeteo'`; when exhausted, serve cache/stale only and set
`meta.quota.pressure = "high"`. The demo has far fewer locations; the guard exists so the app
degrades instead of getting banned.

### 9.5 Provider-specific rules

- **Open-Meteo:** request `timezone=UTC` from the API (conversion done in the app, not by provider),
  `forecast_days` derived from `hours`, `past_days` for history. Parse `current_units`
  and **assert** `carbon_monoxide == "μg/m³"`; if the provider changes units, fail the adapter
  loudly rather than silently mis-scale.
- **OpenAQ:** only if `OPENAQ_API_KEY` set and `ENABLE_OPENAQ=true`. Fetch nearest location within
  15 km; display as a **separate** "Official station" card with distance and timestamp. Never merged
  or averaged with modelled data.
- **CPCB (data.gov.in):** `ENABLE_CPCB=false` by default. Adapter exists, is tested against a
  recorded fixture, and is only enabled after a manual availability check. If enabled, same
  separate-card treatment plus "Official CPCB station" attribution.
- **Routing:** `HaversineRoutingProvider` is the default (great-circle × 1.3 urban circuity, labelled
  "estimated"). OSRM demo server is opt-in via `ENABLE_OSRM`; results carry `source: "osrm"` and
  `is_estimate: true`. No navigation instructions are ever produced.
- **Geocoding:** server-side proxy only; the browser never calls a third party directly (protects
  the quota and avoids CORS surprises).

### 9.6 Freshness semantics (shown verbatim in the UI)

| State | Definition | UI |
|---|---|---|
| `modelled` | CAMS forecast/model output | "Modelled forecast · CAMS · updated 14 min ago" |
| `measured` | Station observation | "Station: Anand Vihar · 2.3 km · 14:00" |
| `stale` | Served from cache beyond TTL | Amber banner: "Showing saved data from 11:20 (2 h old)" |
| `partial` | Some pollutants missing | "Not reported: SO₂, O₃" + AQI coverage list |
| `unavailable` | Nothing usable | "Air-quality data is unavailable right now" + retry, **no numbers** |

---

## 10. Domain calculations (transparent methodology)

All functions in `domain/` are pure, deterministic, and unit-tested against known vectors.

### 10.1 CPCB National AQI

Verified breakpoints (CPCB 2014 methodology, as reproduced by ies.gov.in):

| Category (AQI) | PM2.5 24h | PM10 24h | NO₂ 24h | O₃ 8h | CO 8h (mg/m³) | SO₂ 24h |
|---|---|---|---|---|---|---|
| Good (0–50) | 0–30 | 0–50 | 0–40 | 0–50 | 0–1.0 | 0–40 |
| Satisfactory (51–100) | 31–60 | 51–100 | 41–80 | 51–100 | 1.1–2.0 | 41–80 |
| Moderate (101–200) | 61–90 | 101–250 | 81–180 | 101–168 | 2.1–10 | 81–380 |
| Poor (201–300) | 91–120 | 251–350 | 181–280 | 169–208 | 10–17 | 381–800 |
| Very poor (301–400) | 121–250 | 351–430 | 281–400 | 209–748 | 17–34 | 801–1600 |
| Severe (401–500) | 250+ | 430+ | 400+ | 748+ | 34+ | 1600+ |

Sub-index: `I = I_lo + (I_hi − I_lo) × (C − C_lo) / (C_hi − C_lo)`; `AQI = max(subindices)`;
dominant pollutant = `argmax`; clamp at 500.

Rules:
1. CO is converted µg/m³ → mg/m³ (`/1000`) before indexing. A test pins this; the live probe
   returned 1581 µg/m³ = 1.581 mg/m³.
2. AQI is produced only when **≥ 3 sub-indices** exist and at least one of PM2.5/PM10 is present;
   otherwise `cpcb_aqi = null` with `reason: "insufficient_pollutants"`. (The ≥3 rule must be
   confirmed against the CPCB methodology PDF at implementation.)
3. Averaging windows are respected: the API supplies hourly values; the UI labels the AQI as
   "computed from current hourly values", not as an official 24 h average. This distinction is
   displayed, not hidden.

**Worked example (live probe, 2026-11-18 22:30 IST):**

| Pollutant | Concentration | Sub-index |
|---|---|---|
| PM2.5 | 75.2 µg/m³ | 101 + (75.2−60)/30 × 99 = **151.2** |
| PM10 | 76.4 µg/m³ | 51 + (76.4−50)/50 × 49 = 76.9 |
| NO₂ | 63.7 µg/m³ | 51 + (63.7−41)/39 × 49 = 79.5 |
| SO₂ | 27.9 µg/m³ | 27.9/40 × 50 = 34.9 |
| O₃ | 26.0 µg/m³ | 26.0 |
| CO | 1.581 mg/m³ | 51 + (1.581−1.0)/1.0 × 49 = 79.5 |

→ **AQI 151, Moderate, dominant PM2.5** — while the provider's US AQI reads 166 ("Unhealthy").
The UI shows "Moderate (CPCB 151)" and, separately, "US AQI 166 (different scale)".

### 10.2 Exposure dose (SmartRoutine, EcoRoute)

```
inhaled_µg = Σ_t  C_t[µg/m³] × IR(activity, age_band)[m³/h] × INF(mode) × Δt[h]
```

| Assumption | Values | Status |
|---|---|---|
| Inhalation rate, adult | rest 0.5, light 1.0, moderate 1.5, vigorous 2.4 m³/h | Indicative, derived from US EPA Exposure Factors Handbook; **transcribe and cite exact table** |
| Age multiplier | 0–5 ×1.2, 6–12 ×1.1, 13–17 ×1.0, 18–59 ×1.0, 60+ ×0.9 | Heuristic; labelled as such |
| Infiltration factor | walk/cycle 1.0, bus 0.6, car windows closed 0.5, car recirculation 0.3, metro 0.3 | Indicative; configurable |
| Outdoor concentration | hourly provider value | Modelled data, labelled |

Outputs are shown as **relative exposure index** (car = 100) plus estimated inhaled mass, with the
sentence "Estimate based on modelled air quality and standard breathing rates; not a clinical dose."

### 10.3 Carbon estimation

```
ICE:     kgCO₂e = km × (L/100 km ÷ 100) × EF_fuel[kgCO₂/L] (+ CH₄/N₂O where available)
EV:      kgCO₂e = km × kWh/km × 0.675            # CEA v22.0, FY 2025-26
Transit: kgCO₂e = km × EF_pkm[kgCO₂e/passenger-km]
```

| Factor | Default | Source | Ship status |
|---|---|---|---|
| Petrol combustion | 2.31 kgCO₂/L | IPCC 2006 default | Verify before ship |
| Diesel combustion | 2.68 kgCO₂/L | IPCC 2006 default | Verify before ship |
| Grid electricity (India) | 0.675 kgCO₂/kWh | CEA CO₂ Baseline DB v22.0 | Verified via secondary; transcribe PDF |
| Car petrol consumption | 7.0 L/100 km | User-editable default | Product assumption, labelled |
| Two-wheeler | 2.5 L/100 km | User-editable default | Product assumption, labelled |
| Bus | ≈0.08 kgCO₂e/pkm | To be sourced | **Registry test blocks ship without `source_url`** |
| Metro | ≈0.03 kgCO₂e/pkm | To be sourced | Same |

Every factor lives in `app/factors/*.json`:

```json
{
  "key": "grid_india_cea_v22",
  "value": 0.675,
  "unit": "kgCO2e/kWh",
  "geography": "IN",
  "valid_from": "2025-04-01",
  "version": "CEA-v22.0",
  "source_title": "CO2 Baseline Database for the Indian Power Sector, User Guide v22.0",
  "source_url": "https://cea.nic.in/...",
  "retrieved_on": "2026-11-18",
  "uncertainty": "national weighted average; regional variation ±30%",
  "verified": true
}
```

`scripts/verify_factors.py` fails the build if `source_url` is empty, `version` is empty, a factor is
duplicated, or `verified` is false for a factor used by the UI.

### 10.4 IndoorShield model (mass balance, not a measurement)

Well-mixed steady state:

```
C_indoor = (P × ACH × C_outdoor + E/V) / (ACH + k_dep + CADR/V)
```

| Parameter | Range | Default | Source |
|---|---|---|---|
| Penetration `P` | 0.3–0.8 | 0.5 (windows closed), 0.9 (open) | Literature range; labelled assumption |
| ACH (closed) | 0.3–1.0 /h | 0.5 | Typical residential |
| ACH (windows open) | 3–10 /h | 5 | Typical cross-ventilation |
| Deposition `k_dep` | 0.2–0.5 /h | 0.3 | Literature range |
| Indoor source `E` | cooking/incense | 0 for baseline | Scenario toggle |
| Purifier `CADR` | user input | 0 | Device spec |

Output is an **interval** (low/high from the parameter ranges), never a point value. Actions:
purifier sizing (`CADR ≥ 5 × room volume` for ~5 ACH), ventilation window from the forecast,
kitchen hood/ventilation rules by fuel type (biomass → strong warning), dust management when
`dust` is present.

### 10.5 SmartRoutine engine (greedy, explainable)

1. Enumerate the household's activity windows (morning walk, school run, commute, evening walk)
   from preferences, clamped to daylight-ish hours (05:00–22:00) and the household timezone.
2. For each 30-minute candidate slot, compute exposure using §10.2.
3. Subject to: no overlapping blocks, ≥ 30 min between vigorous activities, school run fixed.
4. Choose the minimum-dose assignment; produce the best and worst alternatives.
5. If the best slot still exceeds the sensitive-group threshold (AQI > 150) or general threshold
   (AQI > 250), flip the activity to an indoor alternative with ventilation/purifier guidance.
6. Attach `rationale[{template_id, params}]` and `fact_refs` to every block — the UI renders these
   without an LLM.

Deterministic and unit-testable: same inputs → same plan. `engine_version` is stored with each plan
so old plans are interpretable after tuning changes.

### 10.6 Module-to-maths map

| Module | Computes | Never claims |
|---|---|---|
| Air Intelligence | CPCB AQI, trends, forecast windows | That CAMS is a sensor |
| Family Intelligence | risk class from age bands + flags | A diagnosis |
| SmartRoutine | exposure-minimising schedule | Medical safety |
| IndoorShield | indoor PM interval, ventilation window | Measured indoor air |
| EcoRoute | CO₂e, relative exposure | Exact route or real-time traffic |
| Impact | kgCO₂e totals with factor provenance | Certified carbon accounting |
| Copilot | phrasing of the above | Any number not in the FactPack |

---

## 11. Security threat assessment

### 11.1 Assets

Gemini key and quota · database credentials · household location · health flags · AI conversation
content · service availability · user trust in numbers.

### 11.2 Threats and mitigations

| # | Threat | Vector | Impact | Mitigation | Residual |
|---|---|---|---|---|---|
| T1 | Prompt injection | Chat message ("ignore instructions…") | Misleading advice | No tools; schema-only output; fact isolation; numeric validator; fallback | Low (useless answer only) |
| T2 | XSS via AI output | Model returns HTML/JS | Session theft | Render as text nodes only; no `innerHTML`; strict CSP; output regex rejects tags | Low |
| T3 | Token theft | XSS, shared device | Data access | 256-bit opaque token, SHA-256 at rest, 30-day TTL, revoke-on-delete, no token in URLs/logs, CSP | Medium (SPA storage tradeoff — see D11) |
| T4 | IDOR | Guessing UUIDs | Cross-user data | Every personal query scoped by `profile_id` from the token; UUIDv4 + ownership check in repository layer | Low |
| T5 | SSRF | Any URL-like input | Internal network access | No user-supplied URLs; fixed upstream hosts; geocoding proxied with query params only | Low |
| T6 | SQL injection | Input fields | DB compromise | SQLAlchemy Core/ORM parameter binding; no string SQL | Low |
| T7 | Mass assignment | Extra JSON fields | Privilege/field abuse | `extra="forbid"`; explicit per-endpoint schemas | Low |
| T8 | DoS / quota drain | Spam air or AI endpoints | Cost, outage | Per-IP + per-token limits; 32 KB body; provider daily budget; AI daily budget; timeouts | Medium |
| T9 | Secret leakage | Committed `.env`, logs | Full compromise | `.gitignore`, `.env.example`, gitleaks, redaction processor, no `NEXT_PUBLIC_*` secrets | Low |
| T10 | CORS abuse | Malicious origin | Unauthorised browser calls | Exact origin allowlist, no wildcard, `Vary: Origin`, bearer auth still required | Low |
| T11 | Dependency compromise | Malicious package | RCE | Pinned versions + lockfiles, Dependabot, `pip-audit`, `npm audit`, no postinstall scripts where possible | Medium |
| T12 | Privacy leak to LLM | Health/location in prompt | GDPR/DPDP exposure | FactPack excludes identifiers; only derived booleans; documented disclosure | Low |
| T13 | Provider impersonation | DNS/TLS | Poisoned data | HTTPS only, certificate validation on, parse-time schema checks | Low |
| T14 | Log-based surveillance | Verbose logs | Privacy harm | No coordinates, messages or tokens in logs; request IDs only | Low |
| T15 | Free-tier data use | Gemini free tier may train on prompts | Confidentiality | Send no identifying context; disclose; paid tier optional | Medium (accepted) |

### 11.3 Token design (D11)

Opaque 32-byte random token, base64url, returned once. Server stores only `sha256(token)`. Browser
stores it in `localStorage` because the frontend (Vercel) and API (Render) are different sites and
third-party cookies are blocked by Safari — an `httpOnly` cross-site cookie would break the demo on
iOS. Compensating controls: strict CSP, no third-party scripts, text-only AI rendering, 30-day
expiry, delete-all endpoint. The alternative (Next.js BFF proxy + same-site cookie) is documented in
§22 as a post-hackathon hardening step.

### 11.4 HTTP security headers (Next.js)

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-<per-request>';
  style-src 'self' 'unsafe-inline'; img-src 'self' data: https://*.tile.openstreetmap.org;
  connect-src 'self' https://<api-host>; font-src 'self'; frame-ancestors 'none';
  base-uri 'none'; form-action 'self'; object-src 'none'
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(self), camera=(), microphone=()
```

`'unsafe-inline'` is limited to styles (Tailwind/Radix inline styles); scripts use nonces.

### 11.5 Secret management

- Server-only env vars; `.env` gitignored; `.env.example` contains placeholders only.
- Startup fails fast if `DATABASE_URL` is missing; Gemini/OpenAQ/CPCB keys are optional and degrade.
- No secret ever reaches the browser bundle (verified by a CI grep for `GEMINI`, `DATABASE_URL` in
  `.next/static`).

---

## 12. Error-handling architecture

### 12.1 Error taxonomy (stable `code` values)

| Code | HTTP | Meaning |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Field-level validation failed (`errors[]` included) |
| `LOCATION_INVALID` | 422 | Coordinates out of range / non-finite |
| `SEARCH_QUERY_INVALID` | 422 | Query length/charset |
| `MESSAGE_INVALID` | 422 | Chat message length/charset/too many URLs |
| `DATE_OUT_OF_RANGE` | 422 | Routine date outside 0–6 days |
| `AUTH_REQUIRED` | 401 | Missing/invalid token |
| `SESSION_EXPIRED` | 401 | Token expired or deleted |
| `CONSENT_REQUIRED` | 403 | Health flag sent without consent |
| `NOT_FOUND` | 404 | Resource not owned or absent (never distinguishes) |
| `CONFLICT` | 409 | Duplicate label |
| `RATE_LIMITED` | 429 | `retry_after` seconds |
| `PROVIDER_UNAVAILABLE` | 503 | No live data and no usable cache |
| `PROVIDER_RATE_LIMITED` | 503 | Upstream 429 with no cache |
| `DATA_INSUFFICIENT` | 200 | Partial data; `cpcb_aqi: null` + reason (not an error) |
| `AI_DISABLED` | 200 | Deterministic answer returned; `ai_disabled_reason` set |
| `AI_BUDGET_EXHAUSTED` | 200 | Same as above |
| `DB_UNAVAILABLE` | 503 | Connection/pool failure |
| `INTERNAL_ERROR` | 500 | Unexpected, logged with `request_id` |

### 12.2 Behaviour matrix

| Condition | Detection | API behaviour | UI behaviour | Log |
|---|---|---|---|---|
| `GEMINI_API_KEY` missing | Boot config | Copilot 200 deterministic, `source: deterministic` | Banner "AI unavailable — showing rule-based guidance" | `warn` once |
| Gemini 429 | HTTP 429 | No retry; fallback answer | Same banner | `warn` + quota metric |
| Gemini 5xx/timeout | Exception | 1 retry (jitter), then fallback | Same banner | `error` |
| Gemini invalid JSON / hallucinated ref | Validator | Discard; fallback | Same banner | `error` with reason |
| Air provider timeout | httpx timeout | Cache if ≤ 24 h → 200 `stale`; else 503 | Stale banner or "unavailable" block | `warn` |
| Air provider 429 | HTTP 429 | Honour `Retry-After`; cache/stale; 503 otherwise | "Data provider is busy" + retry | `warn` |
| Air provider schema change | Pydantic parse | 503 `PROVIDER_UNAVAILABLE`; circuit opens | "Data unavailable" | `error` (alert-worthy) |
| Some pollutants null | Parse | 200, `partial: true`, AQI from ≥3 | "Not reported: …" chips | `info` |
| All pollutants null | Parse | 503 (nothing to show) | "Unavailable" block | `error` |
| Stale cache | `age > TTL` | 200 `stale: true`, `age_minutes` | Amber banner with timestamp | `info` |
| Invalid location | Validation | 422 | Inline field error | `info` |
| Invalid input | Validation | 422 with `errors[]` | Inline, described by `aria-describedby` | `info` |
| DB down | Pool error | `/readyz` 503; endpoints 503 | Global "temporarily unavailable" | `error` |
| Body too large | Middleware | 413 | "Message too long" | `info` |
| Unknown route | Router | 404 problem+json | 404 page with link home | `info` |
| Rate limited | Middleware | 429 + `retry_after` | "Too many requests — try again in Ns" | `warn` |

### 12.3 Non-negotiable invariants

1. **No fabricated measurements.** A missing value is `null`, rendered as "Not reported".
2. **No silent fallback.** Every degradation is labelled in the UI and recorded in `meta`.
3. **No demo data in production paths.** Fixtures exist only under `tests/` and are never imported by
   application code (enforced by an import test).
4. **Errors are actionable.** Each user-visible error states what happened and what to do next, and
   carries a `request_id` for support.

---

## 13. Testing strategy

### 13.1 Pyramid

| Level | Backend | Frontend | Count target |
|---|---|---|---|
| Unit (pure) | `domain/`: AQI, dose, carbon, indoor, routine, factpack, validators | formatting, AQI labels, reducers | ≥ 90 test cases |
| Contract | Provider adapters vs recorded fixtures (`respx`) | API client vs problem+json fixtures | ≥ 15 |
| Integration | FastAPI + real Postgres: auth, CRUD, cascade delete, idempotency, rate limit | MSW-backed feature flows | ≥ 25 |
| E2E | — | Playwright golden paths + a11y | 7 scenarios |
| Non-functional | Import-linter, factor registry, repo size, secret scan | CSP smoke, bundle budget | gates |

### 13.2 Required test vectors (high value)

**AQI (table-driven + property-based):**
- Exact boundaries: 30/31, 60/61, 90/91, 120/121, 250; PM10 250/251; CO 1.0/1.1.
- Live-probe vector: the §10.1 worked example must yield 151 and `dominant_pollutant=pm2_5`.
- Monotonicity: increasing any concentration never decreases its sub-index (Hypothesis).
- Missing-data rule: 2 pollutants → `null`; 3 with PM2.5 → value.
- CO unit scaling: 1000 µg/m³ and 1.0 mg/m³ produce identical sub-indices.

**No-fabrication:**
- Provider returns `null` for SO₂ → API `null`, UI "Not reported".
- Provider raises → API 503 (cold) / 200 `stale` (warm cache).
- Providers fail + no cache → the page must contain **no numeric AQI string** (Playwright assertion).

**AI:**
- Injection corpus: "ignore previous instructions", "reveal your system prompt", "print the API key",
  Base64 payloads, Hindi/Hinglish injection → must never appear in output; citations still valid.
- Hallucinated number ("AQI is 320") not in the pack → fallback.
- Missing key / 429 / timeout → deterministic answer with `ai_disabled_reason`.
- Budget exhaustion → deterministic answer, no API call (asserted via mock).

**Carbon:**
- Known vector: 10 km petrol car at 7 L/100 km → 1.617 kgCO₂e.
- EV: 10 km at 0.15 kWh/km → 1.0125 kgCO₂e.
- Zero-distance and negative input rejected.

**Indoor:**
- Monotonic: higher CADR → lower indoor concentration; higher ACH with high outdoor PM → higher indoor.
- Interval ordering: low ≤ high.

### 13.3 Gates

| Gate | Threshold | Blocking |
|---|---|---|
| Backend coverage | domain ≥ 90% branch, total ≥ 80% | Yes |
| Frontend coverage | ≥ 70% lines | Yes |
| axe (E2E pages) | 0 critical/serious | Yes |
| Lighthouse a11y | ≥ 95 | Soft (report) |
| Bundle (initial route) | ≤ 200 KB gzip | Yes |
| E2E | 100% pass, 0 skipped | Yes |
| Factor registry | 100% have `source_url` + `version` | Yes |

No mutation testing and no visual-regression tooling in the hackathon window — they add runtime
without changing the delivered quality at this scope.

---

## 14. CI/CD architecture

`.github/workflows/ci.yml` (single workflow, path-filtered jobs, `concurrency: cancel-in-progress`):

| Job | Commands | Notes |
|---|---|---|
| `web-static` | `npm ci`, `eslint .`, `prettier --check`, `tsc --noEmit` | Node 24 |
| `web-unit` | `vitest run --coverage` | Fails under thresholds |
| `web-build` | `next build` | With placeholder env; catches RSC/SSR errors |
| `api-static` | `ruff check`, `black --check`, `mypy app`, `bandit -r app -ll` | Python 3.13 |
| `api-test` | `pytest --cov` with `postgres:17` service | Alembic upgrade before tests |
| `contract-drift` | regenerate `openapi.json` + TS types, `git diff --exit-code` | Prevents silent API drift |
| `security` | `gitleaks detect`, `pip-audit`, `npm audit --omit=dev` | Fails on high/critical |
| `repo-hygiene` | size < 10 MB, one branch, no `.env`, no `node_modules` | Requirement §12 |
| `e2e` | compose Postgres + uvicorn + `next start` + Playwright (chromium) | Uploads trace on failure |
| `ci-required` | Aggregate job depending on all above | Single required check |

Branch protection on `main`: required `ci-required`, linear history, no force-push. Work happens on
`main` only (one branch requirement); commits are small and CI runs per push.

Deployment:
- **Web:** Vercel Git integration (production from `main`). Preview deployments disabled for fork PRs.
- **API:** Render auto-deploy from `main`; pre-deploy `alembic upgrade head`.
- **Post-deploy smoke:** `curl /healthz` and `/v1/air/current` for one fixed city; fail the run and
  alert if 5xx.

---

## 15. Deployment architecture

```mermaid
flowchart TB
    subgraph Vercel
      W[Next.js 16 production]
    end
    subgraph Render
      A[FastAPI web service]
      P[(PostgreSQL 17)]
    end
    U[User] --> W
    W -->|HTTPS, Bearer| A
    A --> P
    A --> OM[Open-Meteo]
    A --> G[Gemini]
    W --> OSM[OSM tiles]
```

### 15.1 Environments

| Environment | Web | API | DB | Purpose |
|---|---|---|---|---|
| Local | `next dev` :3000 | `uvicorn --reload` :8000 | Docker Postgres 17 | Development, E2E |
| Production | Vercel | Render | Render Postgres | Demo/judging |

No staging environment: a second API+DB doubles operational work for no judge-visible benefit. PR
checks run the full stack locally in CI.

### 15.2 Environment variables (`.env.example`)

```
# API
APP_ENV=development
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/saans
ALLOWED_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
SESSION_TTL_DAYS=30
OPENMETEO_DAILY_CALL_BUDGET=8000
ENABLE_OPENAQ=false
OPENAQ_API_KEY=
ENABLE_CPCB=false
CPCB_API_KEY=
ENABLE_OSRM=false
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash-lite
AI_DAILY_REQUEST_BUDGET=300

# Web
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 15.3 Operational realities

- **Render free tier sleeps** after idle (~50 s cold start). For judging, either use a paid instance
  for the demo window or run a 10-minute uptime ping. This is a documented, deliberate tradeoff.
- **Free Postgres expires** on Render's free plan; use the paid starter for the judging window or
  keep a nightly `pg_dump` to a local file (never committed).
- **Migrations** run once, pre-deploy, single instance. Migrations must be backward compatible for
  one release (expand → migrate → contract) to allow rollback by redeploy.
- **Backups:** daily automated snapshot (paid) or manual dump before the demo.
- **Observability:** JSON logs (`structlog`) with `request_id`, `route`, `status`, `latency_ms`,
  `validation`, `provider`, `cache`. `/readyz` reports DB + last successful provider fetch.
  No third-party APM in scope.

### 15.4 Local developer experience

```
docker compose up -d db
cd apps/api && python -m venv .venv && pip install -e ".[dev]" && alembic upgrade head && uvicorn app.main:app --reload
cd apps/web && npm ci && npm run dev
```

---

## 16. Performance plan

| Concern | Decision |
|---|---|
| Upstream calls | 2-dp coordinate cache; 30 min current / 3 h forecast / 24 h history |
| Upstream protection | Daily call budget; circuit breaker; `httpx` pool (50 conns); 5 s/8 s timeouts |
| DB | Indexed lookups only; no N+1 (`selectinload`); pool 5 + 5 overflow (fits Render limits) |
| Response size | Forecast trimmed to requested hours; ≤ 72 hourly points; gzip |
| HTTP caching | `ETag` + `Cache-Control: public, max-age=300` for public air reads |
| Frontend JS | Route-level splitting; `dynamic(ssr:false)` for Leaflet and Recharts; no icon barrel imports |
| Images/fonts | `next/font` subset; no large images; logo < 40 KB |
| AI | Prompt ≤ 1,200 tokens; history ≤ 600; output ≤ 350; 15 min response cache |
| Budgets | LCP < 2.5 s (4G), INP < 200 ms, CLS < 0.1, initial JS ≤ 200 KB gzip |

No CDN beyond Vercel's edge, no Redis, no read replicas — none are justified at this scale.

---

## 17. Accessibility plan (WCAG 2.2 AA)

| Requirement | Implementation | Verification |
|---|---|---|
| 1.4.3 Contrast | Tailwind tokens chosen at ≥ 4.5:1; severity colours darkened for text | axe + manual contrast check |
| 1.4.11 Non-text contrast | Icons/borders ≥ 3:1 | Manual |
| 1.4.1 Use of colour | Severity = **text label + icon + numeric** ("Moderate · 151 · ▲") + pattern in charts | Component test asserts label presence |
| 1.4.13 Content on hover | Tooltips dismissible and hoverable | Manual |
| 2.1.1 Keyboard | All interactive elements reachable; map has a non-map alternative (coordinate inputs + saved list) | Playwright keyboard-only flow |
| 2.4.3 Focus order | DOM order matches visual order | Manual |
| 2.4.7 Focus visible | `focus-visible` ring on every control | Manual |
| 2.4.11 Focus not obscured | Sticky header offset handled | Manual |
| 2.5.7 Dragging | Map supports click/keyboard; no drag-only interaction | Manual |
| 2.5.8 Target size | ≥ 24×24 px (40 px for primary actions) | Manual |
| 3.2.6 Consistent help | Help link in the same place on all app pages | Manual |
| 3.3.1 Error identification | Human-readable message + field association | Form tests |
| 3.3.3 Error suggestion | Every error says how to fix it | Copy review |
| 3.3.7 Redundant entry | Household data never re-asked between modules | E2E |
| 3.3.8 Accessible auth | No passwords, no cognitive test (anonymous session) | Design |
| 4.1.2 Name/role/value | Native elements + Radix primitives with labels | axe |
| 4.1.3 Status messages | `aria-live="polite"` for AI answers, saves, plan regeneration | Component test |
| 1.4.4 Resize text | 200% zoom and 320 px width without loss | Manual + Playwright 320 px |
| 2.3.3 Animation | Recharts animations disabled with `prefers-reduced-motion` | CSS test |
| Charts (non-WCAG, good practice) | `<figure>` + `<figcaption>` summary + "View data table" toggle + `aria-describedby` | Component test |

Severity is never encoded by colour alone anywhere — including map markers (letter + shape), chart
lines (dash patterns + labels), and badges (text + icon + value).

---

## 18. Development milestones (10-day hackathon window)

| Day | Milestone | Deliverable | Exit criteria |
|---|---|---|---|
| 1 | M0 Skeleton | Monorepo, CI, docker-compose, `.env.example`, DB up, `/healthz` | CI green on empty app |
| 2 | M1 Data layer | Providers + cache + circuit breaker + `/air/*` + AQI engine | AQI vectors pass; live Delhi call works |
| 3 | M2 Air UI | Air page with chart, provenance, staleness, accessible table | axe clean; provider-down test passes |
| 4 | M3 Household | Sessions, household CRUD, preferences, saved locations | Cascade delete verified |
| 5 | M4 SmartRoutine | Engine + `/routines` + UI with rationale | Deterministic snapshot tests pass |
| 6 | M5 IndoorShield | Indoor model + assessment UI + ventilation windows | Interval ordering + monotonicity tests |
| 7 | M6 EcoRoute + Impact | Routing/carbon/exposure + factor registry + impact UI | Factor gate passes; known vectors pass |
| 8 | M7 Copilot | FactPack, Gemini adapter, validator, fallback, UI | Injection + hallucination suites pass |
| 9 | M8 Hardening | Perf, CSP, rate limits, a11y sweep, E2E suite | All gates green; bundle budget met |
| 10 | M9 Ship | README, docs, deploy, demo script, dry run | Public URL passes smoke + judge script |

Buffer: none. Scope cuts, if forced, in this order: EcoRoute routing (fall back to haversine only),
history view, saved locations. **Never cut:** data honesty, AQI correctness, a11y basics, tests.

---

## 19. Technical risks and mitigations

| # | Risk | L | I | Mitigation | Early warning |
|---|---|---|---|---|---|
| R1 | Gemini free-tier quota or model retirement breaks the demo | H | M | AI optional; deterministic fallback; model in env; budget guard; smoke test | Copilot shows "AI unavailable" during rehearsal |
| R2 | Render cold start during judging | H | M | Paid instance for demo window or uptime ping; skeleton UI while waking | First request > 3 s |
| R3 | CAMS coarse resolution makes hyperlocal claims wrong | H | H | Never claim hyperlocal; show grid cell; label "modelled"; distance/uncertainty copy | Judges ask "is this my street?" |
| R4 | CPCB/OpenAQ unavailable | H | L | Off by default; separate card; no dependency | Adapter errors in logs |
| R5 | Open-Meteo rate limit or terms change | L | H | Call budget, cache, attribution, provider abstraction | 429s in fetch log |
| R6 | OSM tiles blocked for excessive use | L | M | Attribution, low zoom usage, graceful "map unavailable" fallback | Tile 403s in browser console |
| R7 | Health claims overreach | M | H | Non-medical language lint, disclaimer, no diagnosis verbs | Copy review |
| R8 | Scope creep across 7 modules | H | H | Milestones with hard exits; cut order defined | Day 6 with < 4 modules done |
| R9 | Emission factors challenged by judges | M | H | Registry with URLs, versions, uncertainty, "how we calculate" panel | Any factor without source |
| R10 | Accessibility of charts/maps | M | M | Table fallback, text severity, keyboard paths | axe failures |
| R11 | Privacy objection (location/health) | M | M | Minimisation, rounded coords, consent, delete-all, disclosure | User confusion on consent screen |
| R12 | TS 5.9 vs Next 16 incompatibility | L | M | Verified peer range; pin; upgrade path documented | `tsc` errors on scaffold |
| R13 | JSONB plan schema drift | M | M | `engine_version` + Pydantic validation on read; old plans expire in 90 days | Validation errors after deploy |
| R14 | Timezone/DST errors | M | M | Store UTC, compute in household TZ with `zoneinfo`, tests for IST | Off-by-5:30 in routine times |

---

## 20. Acceptance criteria

### Module 1 — Air Intelligence
- [ ] Search by name returns ≤ 8 places with country/state; selecting one loads readings.
- [ ] Displays PM2.5, PM10, CO, NO₂, SO₂, O₃ with units and "Not reported" for nulls.
- [ ] CPCB AQI, category, and dominant pollutant are shown; category is text + icon + number.
- [ ] Forecast chart covers 24/48/72 h with a data-table alternative and a written summary.
- [ ] Provenance shows provider, modelled/measured, observation time, age, and attribution.
- [ ] Stale data shows an amber banner with the timestamp; unavailable data shows no numbers.
- [ ] US/EU AQI, if shown, is labelled "different scale".
- [ ] History is capped at 90 days with an explanatory note.

### Module 2 — Family Intelligence
- [ ] Household can be created without any name, email or phone.
- [ ] Members accept age bands and optional health flags; health flags are rejected without consent.
- [ ] Preferences cover activity types, commute mode, and units.
- [ ] "Delete all my data" removes profile, household, plans, logs, and conversations (verified by query).
- [ ] Risk classification is explainable ("child under 5 + asthma → sensitive group").

### Module 3 — SmartRoutine AI
- [ ] Plan for a date is generated deterministically and is idempotent for identical inputs.
- [ ] Every block shows start/end, venue, exposure index, and a plain-language rationale.
- [ ] At least one alternative is shown when the best window is not ideal.
- [ ] If all windows exceed the threshold, an indoor alternative is proposed.
- [ ] Rationale is available with AI disabled (no LLM needed).

### Module 4 — IndoorShield AI
- [ ] Indoor estimate is an interval and is labelled an estimate, not a measurement.
- [ ] Purifier sizing uses room volume and CADR; guidance changes with inputs.
- [ ] Ventilation recommendation uses the forecast's cleanest 2-hour window.
- [ ] Kitchen guidance varies by fuel type; biomass triggers a strong warning.
- [ ] Outdoor data unavailability still yields indoor-source guidance (no fabricated outdoor value).

### Module 5 — EcoRoute AI
- [ ] Compares ≥ 4 modes with distance source labelled (`estimated` or `osrm`).
- [ ] Shows CO₂e, duration, and relative exposure index for each mode.
- [ ] States the tradeoff explicitly when the lowest-carbon mode is not the lowest-exposure mode.
- [ ] Handles identical origin/destination and out-of-range coordinates with clear errors.
- [ ] Never presents itself as navigation.

### Module 6 — Impact Intelligence
- [ ] Every logged activity stores factor key, value, version, and source URL.
- [ ] Summary breaks down by category and shows the total formula.
- [ ] "How we calculated this" lists each factor with its source link.
- [ ] Deleting an activity updates the summary immediately.
- [ ] No tree-offset or equivalency gimmicks; only documented factors.

### Module 7 — SAANS AI Copilot
- [ ] Answers cite fact IDs; the UI renders server-side citations, not model text.
- [ ] Every numeric claim in an answer is traceable to the FactPack (automated test).
- [ ] With the key removed, the copilot still answers with labelled deterministic guidance.
- [ ] Injection prompts never produce system-prompt leakage, URLs, or fabricated numbers.
- [ ] Conversation deletion removes all messages.

### Cross-cutting
- [ ] CI green: lint, format, types, unit, integration, E2E, a11y, security, size.
- [ ] Repo public, one branch, < 10 MB, no secrets, `.env.example` present, README complete.
- [ ] Lighthouse a11y ≥ 95; axe 0 critical/serious.
- [ ] No screen renders a measurement when the provider failed.

---

## 21. Uncertainties and verification plan

| # | Uncertainty | Why it matters | How to verify (step) | If verification fails |
|---|---|---|---|---|
| U1 | Gemini free-tier RPD/RPM per model | AI could stop working mid-demo | AI Studio console + 1-request smoke test with the chosen model | Raise budget/paid tier or default to deterministic mode |
| U2 | Gemini SDK call shape in 3.5.0 | Wrong parameter names break the copilot | `python -c` smoke test with `response_mime_type` + `response_json_schema` | Switch to `interactions.create` + `response_format` in the adapter |
| U3 | Gemini free-tier training on prompts | Privacy disclosure accuracy | Read current terms in AI Studio | Send even less context; add explicit consent text |
| U4 | Open-Meteo caching/storage permission | Legal compliance | Read CAMS/Open-Meteo licence pages | Reduce cache to in-memory only for the session |
| U5 | OpenAQ India station coverage | Whether "official station" card ever shows data | `/v3/locations?country=IN&limit=5` with key | Keep disabled by default |
| U6 | CPCB data.gov.in schema/uptime | Optional provider viability | Request with key, inspect fields and `last_update` | Keep disabled; document |
| U7 | CEA v22.0 exact factor row | Carbon accuracy | Open the official PDF, transcribe table row | Use last verified version, update `valid_from` |
| U8 | WHO AQG exact values | Health reference line | Transcribe from WHO 2021 PDF | Remove reference line (do not guess) |
| U9 | CPCB AQI ≥3-pollutant rule | When to return null | Read CPCB AQI methodology PDF | Adjust rule; update tests |
| U10 | Open-Meteo returns `dust` | IndoorShield dust feature | Live call with `hourly=dust` | Hide dust guidance |
| U11 | OSM tile usage limits | Map may break on demo day | Review tile policy; monitor 403s | Static fallback / disable map |
| U12 | Render free-tier sleep | Demo cold start | Time a cold request | Paid instance or keep-alive |
| U13 | TS 5.9 / Next 16 / ESLint 10 compatibility | Build may fail on scaffold | `create-next-app` + `tsc` + `eslint` on day 1 | Pin to Next 15 LTS line |
| U14 | DPDP Act consent wording | Compliance | Legal review (out of scope) | Publish conservative copy; minimise data |

Each uncertainty has an owner task in Milestone M0/M1; none blocks the blueprint.

---

## 22. Approval gates for Step 2

Before implementation, please confirm these five decisions (recommendations in bold):

1. **Identity model:** anonymous device session with opaque bearer token (**recommended**) vs. email
   accounts. Anonymous keeps PII at zero and is faster/safer for a hackathon.
2. **Default AI model:** `gemini-3.5-flash-lite` (**recommended**, lowest cost with a free tier) vs.
   `gemini-4-hydrogen` (higher quality, ~5× cost, free tier reported).
3. **CPCB integration:** keep the data.gov.in adapter disabled by default (**recommended**) vs. block
   the build until it is live. The adapter is written either way.
4. **Language:** English only with all copy centralised in `messages/en.ts` (**recommended**) vs.
   English + Hindi in this build. Hindi adds ~1.5 days (copy, review, layout checks).
5. **Routing:** estimated distance (haversine × 1.3) with optional OSRM (**recommended**) vs.
   OSRM required. Requires no SLA dependency.

If you approve, **Step 2** will be, in this order:
1. Scaffold `apps/web` + `apps/api` at the pinned versions, `docker-compose` Postgres, `.env.example`,
   `/healthz`, and a green CI pipeline (Milestone M0).
2. Implement `domain/aqi.py` + the provider layer with recorded fixtures and the live smoke script —
   the correctness core first, before any UI.
3. Build Module 1 end-to-end (API → typed client → accessible page), then proceed module by module
   per §18.

No code has been written and no dependencies have been installed. Awaiting approval to proceed.

