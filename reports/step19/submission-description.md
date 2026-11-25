# SAANS SAATHI AI — Hackathon Submission Description

## Project Name
SAANS SAATHI AI

## Tagline
Every Breath Matters. Every Decision Counts.

## Problem Statement

Urban air pollution represents one of the most significant environmental health risks globally, with the World Health Organization estimating that 99% of the world's population breathes air that exceeds WHO guideline limits. In Indian urban contexts, particulate matter (PM2.5, PM10), nitrogen dioxide (NO₂), sulfur dioxide (SO₂), carbon monoxide (CO), and ozone (O₃) regularly exceed safe limits, contributing to respiratory and cardiovascular diseases.

Despite the availability of air-quality data through various platforms, several barriers prevent individuals from effectively using this information:

- **Data fragmentation**: Air-quality information is scattered across different apps, websites, and government portals with inconsistent formats and standards
- **Technical barriers**: Many platforms require domain knowledge to interpret AQI values, understand pollutant concentrations, and assess health implications
- **Lack of personalization**: Most tools provide generic data without considering individual circumstances (location, health conditions, daily routines, family composition)
- **Fragmented decision-making**: Translating air-quality information into everyday decisions (whether to exercise outdoors, how to travel, ventilation decisions) requires knowledge that most people don't possess
- **Privacy concerns**: Many air-quality platforms require account creation, personal information collection, and continuous tracking
- **Model-presented-as-live**: Several platforms present model-based forecasts as live ground-station measurements without proper provenance or uncertainty communication

**Families face additional challenges**: Coordinating decisions across household members, considering diverse health conditions (asthma, allergies, COPD, heart conditions), and planning daily activities (school runs, work commutes, outdoor exercise) while accounting for air quality adds complexity that existing tools don't address.

SAANS SAATHI AI solves these problems by providing an integrated, privacy-conscious platform that translates environmental information into personalized, actionable decisions for everyday breathing and living.

## Proposed Solution

SAANS SAATHI AI is a full-stack urban air-quality and sustainable-living intelligence platform with seven integrated modules:

### 1. Air Intelligence
Provides detailed air-quality analysis including CPCB 2014 National AQI, pollutant concentrations (PM2.5, PM10, NO₂, SO₂, CO, O₃) with provider labels and observation timestamps. Clearly distinguishes model-based forecast data from ground-station observations; reports unavailable data with explicit reasons rather than fabricating readings.

### 2. Family Intelligence
Enables anonymous household profile creation with health consent management and preference-based recommendations. Designed around session-based anonymity — no accounts, no emails, no phone numbers. Health flags (asthma, allergy, COPD, heart condition, pregnancy) are optional and add general precautions to activity guidance without medical diagnosis.

### 3. SmartRoutine AI
Deterministic daily schedule planner that stores activities with fixed and flexible time windows. Orders activities by start time and provides timing guidance advisory ("Timing guidance is not connected — exposure-aware scheduling needs current air-quality data"). Supports up to 12 activities with timezone-aware start times.

### 4. IndoorShield AI
Indoor environment assessment with an 8-item shelter checklist. Explicitly states "no indoor sensor data is claimed" and provides general ventilation guidance ("Ventilate when outdoor PM2.5 is lowest, typically early morning in many Indian cities. This is general guidance, not a reading from a sensor in your home."). All recommendations include appropriate disclaimers.

### 5. EcoRoute AI
Transportation mode comparison with DEFRA 2023 / IPCC 2006 / CEA v22 emission factors. Displays comparison results with clear disclaimers ("No route is drawn or scored on this device. Pollution exposure is only shown when the comparison service returns an exposure index built from real air-quality data; otherwise the column stays empty."). Unsupported modes return null, never invented numbers.

### 6. Impact Intelligence
Sustainability activity logging with full provenance disclosure. User-entered quantities are displayed as quantities entered, not computed savings. Baseline assumptions are explicitly labelled as modelled assumptions, not measured values. Emission factor sources (DEFRA 2023, IPCC 2006, CEA v22) are always shown with version and retrieval date.

### 7. SAANS AI Copilot
Grounded AI conversation that cites application data via FactPack. Fail-closed when Gemini service is unavailable ("When the service is unavailable, no answer is generated here"). Constrained output schema prevents hallucination, prompt injection, and unauthorized tool execution. Medical disclaimers consistently applied. Domain grounding ensures responses stay within platform scope.

## Technology

### Frontend
- **Next.js 16** + **React 19** + **TypeScript 5.9.3** + **Tailwind CSS 4.3.5**
- **Zod 4.6.7** for schema validation (environment configuration, API client requests)
- **Radix UI primitives** for accessible components (dialogs, accordion, checkboxes, dropdowns, popovers, tabs, switches)
- **Vitest 5.1.1** + **React Testing Library** for unit and integration testing (143 tests across 27 files)
- **Playwright** for end-to-end browser testing (2/2 smoke tests pass; all 11 routes verified with 0 console errors, 0 failed HTTP requests)
- **Responsive layouts** across 6 viewports (360×800 through 1920×1080)

### Backend
- **FastAPI 0.164.0** with **uvicorn[standard] 0.54.0** on Windows with `selector_loop_factory`
- **SQLAlchemy 2.x** ORM with **Pydantic v2 2.14.3** schema validation
- **PostgreSQL 16.15** with two isolated databases (`saans_dev`, `saans_test`)
- **Alembic 9-revision migration chain** (`0009_constraint_names` fixes check-constraint name drift)
- **structlog 26.1.0** for structured logging (no PII in output)
- **httpx 0.28.1** for HTTP client calls to external providers
- **Rate limiting**: Per-integration daily budgets + per-request timeouts
- **Body size limit**: 32 KB `BodySizeLimitMiddleware`
- **CORS allowlist**: `localhost, 127.0.0.1, testserver` (no wildcard)

### AI & Data Services
- **Google Gemini API**: Optional; fail-closed when not configured; deterministic fallback always functional
- **Open-Meteo**: Model-based forecasts (current, history, forecast); cache TTL 30m/3h/24h; always labelled "model-based data"
- **DEFRA 2023**: Verified emission factors for EcoRoute and Impact modules
- **IPCC 2006**: Verified emission factors for EcoRoute and Impact modules
- **CEA v22**: Verified emission factors for EcoRoute and Impact modules
- **CPCB 2014 National AQI**: Currently disabled (`CPCB_ENABLED = False`); reported as `status: "unavailable"` with reason; never mixed with other standards

### Architecture
- **Modular FastAPI**: 107 source files; 34 API routes across 11 prefix groups
- **Pure-function domain engines**: routine-2.0.0, indoor-shield-1.0.0, DEFRA/IPCC/CEA factors, CPCB AQI calculator
- **Session-scoped ownership**: Anonymous bearer token (SHA-256 digest); no user accounts
- **RFC 9457 exception responses** throughout
- **Database connection pool**: `pool_size=5, max_overflow=5, pool_timeout=10s`
- **WindowsSelectorEventLoopPolicy**: Required for uvicorn stability on Windows

### Data Integrity Principles
- **Provenance preservation**: All environmental values have source type, observation time, and freshness stated
- **Model-forecast distinction**: Model output always labelled "model-based data"; ground-station observations labelled with source name
- **No mixed AQI standards**: CPCB 2014 National AQI kept separate; never remapped onto US/European scales
- **No arbitrary AQI calculation**: Only computed when CPCB methodology requirements met (averaging windows + pollutant count); otherwise `aqi_unavailable_reason` explained
- **Emission factor sourcing**: DEFRA 2023, IPCC 2006, CEA v22; unsupported modes → `None`; never guessed or invented
- **User-entered data clarity**: Impact log quantities are the values entered, not computed savings; baseline assumptions labelled as modelled

## GenAI Integration

Google Gemini is integrated as an optional enhancement to the SAANS AI Copilot module, providing conversational assistance grounded in application data.

### Implemented Functionality
- **Constrained conversation UI** on `/copilot` route
- **FactPack grounding**: All responses must cite application data facts (no independent AQI calculation, no sensor invention, no emission factor invention)
- **Fail-closed behavior**: When Gemini service unavailable, page displays: "When the service is unavailable, no answer is generated here"
- **Prompt injection protection**: 
  - Constrained JSON schema (`_RESPONSE_SCHEMA`) enforces `answer`, `actions` (max 5), `avoid` (max 3)
  - `extra="forbid"` on all Pydantic models (`DraftAction`, `DraftAvoid`, `AiDraft`)
  - Two-stage validation: `json.loads()` → `parse_and_validate()` against `AiDraft` model
  - System instruction never receives user text
- **Medical disclaimer consistency**: "These flags add general precautions. They are not a diagnosis or a medical assessment."
- **Domain grounding**: Out-of-domain questions handled by fallback; no hallucination on unrelated topics

### Configured but Unverified
- **Live Gemini responses**: Not configured in current execution environment (API key missing)
- **Real-time AI explanations**: Would require Gemini API key configuration
- **Enhanced conversation depth**: Would require key configuration; current fallback provides deterministic grounded responses

### Not Implemented (Planned Capabilities - Not Currently Active)
- **Independent AQI calculation by AI**: Explicitly prohibited; deterministic backend handles all AQI
- **Sensor data invention by AI**: Explicitly prohibited; FactPack grounded only
- **Route/exposure value invention by AI**: Explicitly prohibited; EcoRoute states "no route is drawn or scored"
- **Savings computation by AI**: Explicitly prohibited; Impact log states "amounts are quantities entered, not savings"

**GenAI declaration**: The application uses Google Gemini API as an optional component for grounded conversation in the SAANS AI Copilot module. When configured, Gemini output is constrained via structured schema and grounded against validated application data (FactPack). When unavailable, the system fails closed with a clear communication of limitation. No unverified or fabricated data is ever presented as live or official.

## Impact

SAANS SAATHI AI aims to deliver the following user and environmental benefits:

### User Benefits
- **Informed daily decisions**: Evidence-based choices about outdoor activities, travel modes, and indoor ventilation
- **Family coordination**: Shared household profile enables coordinated decision-making across family members with diverse health conditions
- **Accessibility**: No technical expertise required; clear language, disclaimers, and guidance
- **Privacy**: No account required; no personal information collected; anonymous session-based operation
- **Reliability**: No fabricated readings; all data provenance explicitly stated; unavailable data honestly reported
- **Actionable guidance**: Concrete recommendations with clear source attribution and freshness information

### Environmental & Social Benefits
- **Increased awareness**: More people engaged with air-quality information through accessible presentation
- **Health-conscious decisions**: Users make choices that reduce pollution exposure, particularly vulnerable populations (children, elderly, those with respiratory conditions)
- **Sustainable transportation**: EcoRoute enables comparison of transportation modes based on carbon emissions, supporting lower-carbon choices
- **Sustainability tracking**: Impact Intelligence helps users understand their sustainability actions with proper disclosure of assumptions

### Intended Impact Scope
- **Primary**: Individual and family-level decision support in urban environments
- **Secondary**: Increased environmental health literacy through accessible presentation
- **Tertiary**: Contribution to awareness of air-quality issues and sustainable living practices

**No measured environmental impact statistics are claimed**. All benefits are qualitative and based on user-facing design principles.

## Future Scope

### Verified Data Source Expansion
- Enable CPCB 2014 AQI with verified API key integration
- Additional city coverage beyond current India-focused configuration
- Real-time ground-station observations when CPCB endpoints become accessible
- Additional verified environmental data providers

### AI Enhancement (with Configured Key)
- Live Gemini responses for grounded conversation (currently deterministic fallback)
- More personalized AI personalization with configured API key
- Advanced route-level exposure data with real-time air-quality feeds
- Natural language query understanding for all module data

### Feature Expansion
- **Real indoor sensors**: Integration with particulate matter, CO₂, VOC sensors (with explicit user consent and "no sensor data claimed" disclaimers)
- **Multi-city support**: Expansion beyond current India focus
- **Advanced route planning**: Real-time pollution exposure along calculated routes
- **Calendar integration**: import/export of routine activities with timezone handling
- **Multi-child family profiles**: Extended household modeling for larger families
- **School-run optimization**: Activity planning around school schedules and air quality
- **Work-from-home recommendations**: Activity planning based on daily air quality forecasts

### Roadmap Prioritization
1. **CPCB AQI re-enablement** with verified API key (highest priority — core data functionality)
2. **Gemini API key configuration** (medium priority — enhances Copilot but not essential)
3. **Production deployment** (medium priority — required for live demo)
4. **Multi-device sync** (lower priority — design currently session-scoped intentional)
5. **Additional module features** (lower priority — incremental enhancements)

## Submission Form Fields — Prepared Values

| Field | Prepared Value |
|-------|---------------|
| Project Name | SAANS SAATHI AI |
| Tagline | Every Breath Matters. Every Decision Counts. |
| Challenge | PromptWars Virtual Challenge 6 |
| Category | Urban Air Quality Assistant |
| Problem Statement | Urban air pollution prevents individuals from making informed daily decisions; fragmented data, lack of personalization, privacy concerns, and model-presented-as-live are common barriers |
| Proposed Solution | SAANS SAATHI AI provides an integrated, privacy-conscious platform with seven modules converting environmental data into personalized, actionable decisions |
| Seven Core Modules | Air Intelligence, Family Intelligence, SmartRoutine AI, IndoorShield AI, EcoRoute AI, Impact Intelligence, SAANS AI Copilot |
| Technology Stack | Next.js 16 + React 19 + TypeScript + Tailwind CSS; FastAPI + SQLAlchemy 2.x + PostgreSQL; Google Gemini (optional); Open-Meteo; DEFRA/IPCC/CEA emission factors |
| GenAI Integration | Google Gemini API used optionally in SAANS AI Copilot; constrained via FactPack and schema; fail-closed when unavailable; no independent AQI calculation; no sensor data invention |
| Repository | GitHub: `0a22cc4` on `main`; 359 files; 2.45 MB |
| Live Application | Development: `http://localhost:3000`; Production: Not yet deployed |
| Demo Video | Not yet recorded (requirement unconfirmed) |
| Changes Description | Initial development through release-candidate stage; 10 root-cause fixes; all quality gates pass except backend coverage 77.53% vs 80% CI gate (documented); all 7 modules implemented with working backends and frontend pages |
| LinkedIn Post | Not applicable (requirement unconfirmed) |

## Known Limitations (Included for Transparency)

- Backend coverage 77.53% vs 80% CI gate — documented limitation; tests not suppressed
- Production deployment unverified — no account access, no deploy config files
- Gemini API key not configured — optional; deterministic fallback always functional
- CPCB 2014 AQI data unavailable — reported as `status: "unavailable"`; no fabricated readings
- Single household per anonymous session — intentional design
- Impact frontend local-only — backend has full endpoints; documented scope limitation
- No HTTPS in development — `http://localhost` used; `https` required for production
- No demo video recorded — challenge requirement (unconfirmed from portal)

## Certification

All environmental data provenance is preserved. No fabricated readings are displayed. CPCB 2014 AQI is reported as unavailable with reason when methodology requirements are not met. Model-based forecasts are always labelled separately from ground-station observations. Emission factors are sourced (DEFRA 2023, IPCC 2006, CEA v22); unsupported modes return null. The application is structured for WCAG 2.2 AA accessibility. All quality checks pass except the backend coverage CI gate, which is documented.

---

*Submission description prepared as part of Step 19 — Final Release Preparation on 2026-11-22. All claims are evidence-based and supported by documentation in the repository.*