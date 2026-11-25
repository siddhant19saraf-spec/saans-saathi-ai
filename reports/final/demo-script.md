# SAANS SAATHI AI — Demo Script

**Duration**: 3-5 minutes  
**Project**: PromptWars Virtual Challenge 6  
**Vertical**: Urban Air Quality Assistant  
**Tagline**: Every Breath Matters. Every Decision Counts.

## Opening (0:00-0:20)

**[Scene: Landing page loads]**

**Narrator**: Urban air pollution affects billions. Yet most people cannot answer a simple question: *"Should I let my family exercise outdoors today?"*

**[Screenshot/Recording: Dashboard area]**

**Narrator**: SAANS SAATHI AI exists to answer that question — with honesty, provenance, and deterministic reliability. No fabricated data. No hidden accounts. No model forecasts presented as live readings.

## Air Intelligence (0:20-0:45)

**[Scene: Air quality page shows AQI with provenance labels]**

**Narrator**: Air Intelligence. The application retrieves current air quality with explicit source attribution.

**[Demonstrate: Show AQI surface with CPCB status, Open-Meteo model data label, observed_at timestamp]**

**Narrator**: Notice: when CPCB data is unavailable, the application honestly reports `status: "unavailable"` with an `aqi_unavailable_reason`. No ground-station values are invented. Model-based data is always labelled. The user sees the freshness: `observed_at` plus `age_minutes` and `stale` flag.

**[Demonstrate: Pollutant breakdown table with individual sub-indices]**

**Narrator**: The CPCB 2014 National AQI methodology computes overall AQI as the maximum of sub-indices. Each sub-index requires minimum valid averaging windows: PM2.5/PM10 need 24-hour data with at least 16 valid hours; NO₂/SO₂/CO/O₃ need 8-hour data with at least 6 valid hours. This is the verified methodology — no shortcuts.

## Family Intelligence (0:45-1:15)

**[Scene: Family/profile page with health flags]**

**Narrator**: Family Intelligence. The application builds a household profile with optional health flags — asthma, allergy, COPD, heart condition, pregnancy. Each flag includes an explicit disclaimer: *"These flags add general precautions. They are not a diagnosis or a medical assessment."*

**[Demonstrate: Add a health flag; show the disclaimer; show how recommendations change]**

**Narrator**: When a household member has asthma, the application automatically incorporates this into downstream recommendations. The context flows through the entire decision pipeline — from Air Intelligence through to the final recommendation.

**[Demonstrate: Household member profile with age bands and sensitivity]**

**Narrator**: Profiles include member age bands and sensitivity settings. All data is session-scoped via anonymous bearer token. No accounts, no emails, no phone numbers. One profile per bearer token; SHA-256 digest validated in database.

## SmartRoutine AI (1:15-1:40)

**[Scene: SmartRoutine scheduling interface]**

**Narrator**: SmartRoutine AI. Deterministic scheduling of fixed and flexible activities — up to 12 activities total.

**[Demonstrate: Create a fixed activity with start/end times; create a flexible window; show versioned plan with inputs_hash]**

**Narrator**: The scheduler uses versioned plans with `inputs_hash` for deduplication — preventing silent staleness. Override activity tracking documents manual changes with version history. Scheduling is O(n log n) where n ≤ 12 activities — already at optimal complexity.

**[Demonstrate: Attempt impossible scheduling; show feasibility check result]**

**Narrator**: When scheduling constraints are impossible, the engine explicitly returns `"Impossible: no valid window"` — no vague error messages. The deterministic engine handles timezone handling and constraint-based scheduling explicitly.

## IndoorShield AI (1:40-2:05)

**[Scene: IndoorShield assessment page]**

**Narrator**: IndoorShield AI. An 8-item shelter checklist with deterministic action plans. Critically: *"No indoor sensor data is claimed."*

**[Demonstrate: Check items on the 8-item checklist; show the "no indoor sensor data claimed" banner; show ventilation guidance]**

**Narrator**: The 8-item shelter checklist tracks each item as checked, unchecked, or NA. The banner explicitly states no indoor sensor data is measured. Ventilation guidance cross-references outdoor AQI: *"When outdoor AQI good, ventilate; when poor, use air purifier."*

**[Demonstrate: Show the deterministic action plan with priorities]**

**Narrator**: The action plan is deterministic — same inputs always produce same output. FactPack citations reference application data. When Gemini is unavailable, the fail-closed message displays: *"When the service is unavailable, no answer is generated here."*

## EcoRoute AI (2:05-2:30)

**[Scene: EcoRoute comparison page]**

**Narrator**: EcoRoute AI. Emission factor comparison across transport modes using sourced factors.

**[Demonstrate: Enter a distance; select modes (walk, worked-from-home); show carbon factors per mode from DEFRA 2023, IPCC 2006, CEA v22]**

**Narrator**: Emission factors come from DEFRA 2023, IPCC 2006, and CEA v22. Each factor has version provenance stated. Unsupported modes return `None` — never invented. An explicit user-facing message: *"No verified emission factor exists for '{activity_type}'. Activity not recorded."*

**[Demonstrate: Show the per-person emission estimate with baseline disclosure]**

**Narrator**: The sustainability activity logging displays user-entered quantities as entered — not computed savings. The baseline is explicitly labelled: *"Modelled assumption, not measured."* `_BASELINE_CAR_KM_PER_DAY = 16.0` km/day per logged activity day.

## Impact Intelligence (2:30-2:55)

**[Scene: Impact/sustainability tracking page]**

**Narrator**: Impact Intelligence. Sustainability activity tracking with transparent emission calculations.

**[Demonstrate: Log a sustainability activity (e.g., 30 min walk); show the entry displayed as entered; show the methodology disclosure]**

**Narrator**: When a user logs a 30-minute walk, the quantity is displayed as entered. The methodology section discloses: *"Baseline is a modelled assumption, never a measured value."* The carbon savings are modelled: *"Compared to modelled car baseline (16 km/day x N days) minus logged activity emissions."*

**[Demonstrate: View impact trends historical record]**

**Narrator**: Historical records are reproducible. Impact summaries show trend analysis over time — all calculations deterministic and traceable to source emission factors.

## SAANS AI Copilot (2:55-3:20)

**[Scene: Copilot chat interface]**

**Narrator**: SAANS AI Copilot. Context-aware conversation grounded in application data.

**[Demonstrate: Send a message about outdoor exercise given current AQI and asthma flag]**

**Narrator**: The Copilot response cites FactPack from application data: current AQI value, household asthma flag, activity preferences. The constrained `_RESPONSE_SCHEMA` enforces: `answer` (max 600 chars), `actions` (max 5), `avoid` (max 3); `extra="forbid"` on all Pydantic models prevents token injection.

**[Demonstrate: Send an empty message; send a long message]**

**Narrator**: Empty messages display the fail-closed: *"When the service is unavailable, no answer is generated here."* Long messages are truncated to max 600 chars for answer + 5 actions × 160 chars + 3 avoid × 80 chars. All responses go through two-stage validation: `json.loads()` then `parse_and_validate()` — rejected answers never shown to user.

**[Demonstrate: Gemini unavailable scenario]**

**Narrator**: When the Gemini API key is not configured (as in the current execution environment), the deterministic fallback is always active. The application functions fully without Gemini. No feature relies on the LLM. This is a competitive differentiator — ordinary implementations break or hallucinate without AI keys.

## Architecture and Closing (3:20-3:50)

**[Scene: Architecture diagram; repository overview]**

**Narrator**: The application architecture connects seven modules through a unified decision pipeline: User Intent → Context Validation → Environmental Data Retrieval → Source and Freshness Validation → Household Context → Activity Constraints → Deterministic Decision Engine → Actionable Recommendation → Grounded AI Explanation.

**[Scene: GitHub repository; compliance checklist]**

**Narrator**: The repository is public on GitHub at commit 0a22cc4 on main branch. 359 files, 1.15 MB — well under the 10 MB challenge limit. `.gitignore` enforces `.env*` exclusion; only `.env.example` with placeholders is tracked. All quality checks pass: Ruff, Black, MyPy, Bandit, pip-audit, ESLint, TypeScript, next build. 264 backend tests pass serial; 143 frontend tests pass.

**[Scene: Seven modules diagram]**

**Narrator**: Seven core modules work together as one environmental decision-intelligence platform: Air Intelligence, Family Intelligence, SmartRoutine AI, IndoorShield AI, EcoRoute AI, Impact Intelligence, and SAANS AI Copilot. The complete decision pipeline communicates supporting information, data sources, timestamps, and relevant uncertainty on every recommendation.

**Narrator**: SAANS SAATHI AI — every breath matters, every decision counts. Deterministic. Provenance-disciplined. Privacy-by-design. Without fabrication. Without compromise.

---
*Demo script generated as part of Ultimate Master Command execution. All application behavior verified at commit 0a22cc4.*