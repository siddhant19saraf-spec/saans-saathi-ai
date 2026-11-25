# SAANS SAATHI AI — Final Submission Form

## Project Information

| Field | Value |
|-------|-------|
| **Project Name** | SAANS SAATHI AI |
| **Tagline** | Every Breath Matters. Every Decision Counts. |
| **Challenge** | PromptWars Virtual Challenge 6 |
| **Category** | Urban Air Quality Assistant |

## Problem Statement

Urban air pollution prevents individuals from making informed daily decisions. Common barriers include fragmented air-quality data across different platforms, technical complexity in interpreting AQI values and pollutant concentrations, lack of personalization for individual circumstances (location, health conditions, daily routines), difficulty translating air-quality information into everyday decisions (whether to exercise outdoors, how to travel, ventilation decisions), privacy concerns requiring account creation and personal information collection, and the proliferation of platforms that present model-based forecasts as live ground-station measurements without proper provenance or uncertainty communication. Families additionally face challenges coordinating decisions across diverse health conditions and daily routines.

## Proposed Solution

SAANS SAATHI AI provides an integrated, privacy-conscious platform that translates environmental information into personalized, actionable decisions. The platform consists of seven modular components:

1. **Air Intelligence** — Detailed air-quality analysis with CPCB 2014 National AQI, pollutant concentrations, model-forecast vs. ground-station distinction, provider labels, freshness timestamps, and unavailable-data handling with explicit reasons.

2. **Family Intelligence** — Anonymous household profile creation with health consent management and preference-based recommendations. No accounts, no emails, no phone numbers. Health flags are optional and add general precautions without medical diagnosis.

3. **SmartRoutine AI** — Deterministic daily activity scheduler with fixed and flexible time windows, timezone-aware planning, up to 12 activities, and timing guidance advisory ("not connected — needs current air-quality data").

4. **IndoorShield AI** — Indoor environment assessment with 8-item shelter checklist. Explicitly states "no indoor sensor data is claimed." General ventilation guidance with appropriate disclaimers ("not a reading from a sensor in your home").

5. **EcoRoute AI** — Transportation mode comparison with DEFRA 2023 / IPCC 2006 / CEA v22 emission factors. Displays comparison with clear disclaimers ("no route is drawn or scored"; "pollution exposure only shown when real data available"). Unsupported modes return null.

6. **Impact Intelligence** — Sustainability activity logging with full provenance. User-entered quantities displayed as entered, not computed savings. Baseline assumptions explicitly labelled as modelled, not measured. Emission factor sources always shown.

7. **SAANS AI Copilot** — Grounded AI conversation with FactPack citations. Fail-closed when Gemini service unavailable ("When the service is unavailable, no answer is generated here"). Constrained output schema prevents hallucination and prompt injection. Medical disclaimers consistently applied.

## Technology

- **Frontend**: Next.js 16 + React 19 + TypeScript 5.9.3 + Tailwind CSS 4.3.5
- **Backend**: FastAPI 0.164.0 + SQLAlchemy 2.x + PostgreSQL 16.15 + Pydantic v2 2.14.3
- **AI**: Google Gemini API (optional; fail-closed when not configured; deterministic fallback functional)
- **Data Providers**: Open-Meteo (model-based, always labelled); CPCB 2014 National AQI (currently disabled, reported as unavailable); DEFRA 2023, IPCC 2006, CEA v22 emission factors
- **Testing**: Vitest (143 frontend tests), pytest (264 backend tests serial), Playwright E2E (2/2 smoke tests, all 11 routes verified)
- **Quality Gates**: Ruff, Black, MyPy, Bandit, pip-audit, ESLint, TypeScript, next build all clean
- **Architecture**: Modular FastAPI (107 source files); pure-function domain engines; session-scoped ownership; RFC 9457 exception responses

## GenAI Integration

Google Gemini API is integrated as an optional component in the SAANS AI Copilot module.

- **Implemented**: Constrained conversation UI; FactPack grounding (application data only); fail-closed when unavailable ("When the service is unavailable, no answer is generated here"); prompt injection protection via constrained JSON schema (`extra="forbid"` on all Pydantic models); medical disclaimer consistency ("These flags add general precautions. They are not a diagnosis or a medical assessment."); domain grounding (out-of-domain questions handled by fallback).
- **Configured but unverified**: Live Gemini responses (API key not configured in current environment); real-time AI explanations would require key configuration.
- **Not implemented (planned, not currently active)**: Independent AQI calculation by AI (prohibited — deterministic backend handles all AQI); sensor data invention by AI (prohibited); route/exposure value invention by AI (prohibited); savings computation by AI (prohibited).

**GenAI declaration**: The application uses Google Gemini API optionally in the SAANS AI Copilot module. When configured, Gemini output is constrained via structured schema and grounded against validated application data (FactPack). When unavailable, the system fails closed with clear communication of limitation. No unverified or fabricated data is ever presented as live or official.

## Repository

- **GitHub**: `0a22cc4` on `main`; 359 files (199 backend + marketing/landing + docs + frontend); 2.45 MB tracked; well under 10 MB challenge limit
- **GitHub URL**: `<repository-url>` (to be filled from official portal)
- **Visibility**: Public (required by challenge) or Private (if permitted by challenge rules)
- **Gitignore**: Enforces `.env*` exclusion; only `.env.example` with placeholders tracked

## Live Application

- **Development**: `http://localhost:3000` (Next.js dev server, `.env.local`: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`)
- **Backend**: `http://localhost:8000` (FastAPI uvicorn; PostgreSQL `saans_test` isolated)
- **Production**: Not yet deployed (no Render/Vercel account access in current environment)
- **Production URL**: `<deployment-url>` (to be obtained if required by challenge)

## Demo Video

- **Required**: Unconfirmed (depends on official challenge requirements)
- **Format**: 3-5 minute MP4/WebM of actual browser recording
- **Content**: Working features only; no fake metrics; no API keys; no fabricated readings
- **URL**: `<video-url>` (YouTube unlisted or Vimeo private; to be provided if required)
- **Guide**: `reports/step18/demo-video-guide.md`; `reports/step19/final-demo-script.md`

## Changes Description

Initial development through release-candidate stage (commit `0a22cc4` on `main`). Seven modules implemented with working backends and frontend pages. Ten root-cause fixes with evidence: env schema (localhost rejection), README inaccuracies, 5 lint/type fixes, pytest connection exhaustion, `.env.local` creation. All quality gates pass except backend coverage 77.53% vs 80% CI gate (documented limitation). All 7 modules verified with working backends and frontend pages. Browser application verified with zero blocking defects across all 11 routes and 15 user workflows (14 pass, 1 conditional). No secrets committed. Repository size 2.45 MB.

## Official Rules

- **Deadline**: `<verified-date>` (from official portal)
- **Maximum attempts**: `<verified-number>` (from official portal)
- **GitHub visibility**: `<public/private>` (from official portal)
- **Deployment URL required**: `<yes/no>` (from official portal)
- **Demo video required**: `<yes/no>` (from official portal)
- **GenAI declaration required**: `<yes/no/details>` (from official portal)
- **LinkedIn post required**: `<yes/no/after-submission>` (from official portal)
- **Mandatory form fields**: `<list>` (from official portal)
- **Changes description format**: `<format>` (from official portal)

*For all fields marked `<verified-value>`, the user must confirm from the official PromptWars Virtual Challenge 6 portal. For fields marked `<unconfirmed>`, the current status is unverified and based on prior-phase assumptions.*

## Submission Declaration

I/We declare that:

- All information provided is true and accurate to the best of my/our knowledge.
- No fabricated environmental data, measurements, or performance statistics are included.
- No API keys, passwords, or secret credentials are committed to the GitHub repository.
- The repository respects the challenge's file size and visibility requirements.
- The application demonstrates genuine engineering effort with documented limitations and transparent provenance.
- AI/GenAI integration (Google Gemini) is used optionally with constrained output and fail-closed validation.
- No user accounts, personal emails, or phone numbers are collected (anonymous session-based operation).
- All environmental data provenance is preserved; no mixed AQI standards; no arbitrary AQI calculations.
- This submission is an internal engineering self-assessment (91/100 technical score) and does not guarantee any official hackathon rank or position.
- All remaining limitations are documented in `docs/REAL_WORLD_QA_REPORT.md`, `docs/ULTIMATE_ENGINEERING_REPORT.md`, and `docs/FINAL_SUBMISSION_READINESS.md`.

---

*Submission form prepared as part of Step 19 on 2026-11-22. User must confirm challenge requirements from the official PromptWars Virtual Challenge 6 portal before final submission.*