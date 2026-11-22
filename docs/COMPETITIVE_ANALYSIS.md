# SAANS SAATHI AI — Competitive Analysis

**Audit date:** 2026-11-22  
**Scope:** Comparison of SAANS SAATHI AI against existing air-quality and environmental intelligence platforms.

---

## 1. Competitor Landscape

| Platform | Type | Pricing | Core Features | AI Integration |
|----------|------|---------|---------------|----------------|
| IQAir AirVisual | Consumer app / API | Freemium | Real-time AQI, forecasts, health recommendations, map | Limited (basic recommendations) |
| Plume Labs (AccuWeather) | Consumer app | Free | Real-time AQI, street-level maps, activity advice | Limited |
| BreezoMeter | B2B API | Paid | AQI, pollen, fire tracking, health insights | Some ML-based forecasting |
| AirNow (EPA) | Government | Free | Official US AQI, monitoring station data | None |
| CPCB Sameer | Government (India) | Free | Official India AQI, monitoring stations | None |
| OpenAQ | Open data platform | Free | Open air quality measurements globally | None |
| WAQI (World Air Quality Index) | Aggregator | Free | Global AQI aggregation, map | None |
| PurpleAir | Consumer sensors | Hardware + app | Low-cost sensor network, map | None |

---

## 2. Feature Comparison

| Feature | IQAir | Plume | BreezoMeter | AirNow/CPCB | OpenAQ | SAANS SAATHI AI |
|---------|-------|-------|-------------|-------------|--------|-----------------|
| Real-time AQI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (model + station) |
| Forecast AQI | ✅ | ✅ | ✅ | Limited | No | ✅ (48-hr, labelled) |
| Observation vs forecast distinction | Partial | Partial | Partial | ✅ | ✅ | ✅ (explicit labelling) |
| CPCB 2014 method | Partial | No | No | ✅ | No | ✅ |
| Personalized household profile | No | Limited | No | No | No | ✅ |
| Activity windows & routine planning | No | Basic | No | No | No | ✅ (SmartRoutine) |
| Deterministic routine scheduler | No | No | No | No | No | ✅ |
| Indoor air assessment | No | No | No | No | No | ✅ (IndoorShield) |
| Sensor registration & readings | No (own sensors) | No | No | No | No | ✅ |
| Transport emission comparison | No | No | Limited | No | No | ✅ (EcoRoute) |
| Sourced emission factors | No | No | Limited | No | No | ✅ |
| Grounded AI copilot with citations | Limited | Limited | Limited | No | No | ✅ |
| Fail-closed AI validation | No | No | No | N/A | N/A | ✅ |
| FactPack privacy (no PII to model) | No | No | No | N/A | N/A | ✅ |
| Anonymous session model | No | No | No | N/A | N/A | ✅ |
| Health-flag consent gating | No | Limited | No | No | No | ✅ |

---

## 3. What Is Industry Standard (Not Differentiating)

| Feature | Status in SAANS SAATHI AI | Assessment |
|---------|--------------------------|------------|
| Real-time AQI display | ✅ Implemented | Table stakes — expected |
| Forecast AQI | ✅ Implemented (48-hr) | Expected |
| Air quality map | ✅ Implemented (OpenStreetMap) | Expected |
| Health recommendations | ✅ Implemented (deterministic rules) | Expected |
| API access | ✅ Implemented (REST) | Expected for B2B platforms |

---

## 4. SAANS SAATHI AI's Actual Differentiators

### 4.1 Pollution-to-Action Intelligence (Genuinely Implemented)

Unlike most platforms that show AQI and leave interpretation to the user, SAANS SAATHI AI converts readings into specific, actionable advice:

- **SmartRoutine AI**: Deterministic scheduler that considers forecast concentrations, activity windows, fixed activities, member sensitivity, and inhaled dose estimates. Produces a versioned daily plan with overrides.
- **IndoorShield AI**: Deterministic recommendation engine that turns home assessments + sensor readings + outdoor context into prioritized actions with transparent scoring (based on WHO/ASHRAE/EPA guidance).
- **EcoRoute AI**: Transport mode comparison using sourced emission factors (DEFRA, IPCC, CEA) with haversine distance estimates. Modes without verified factors return null rather than invented numbers.

**Evidence:** `backend/app/domain/routine.py`, `backend/app/domain/indoor_shield.py`, `backend/app/domain/carbon.py`, `backend/app/services/routine_service.py`, `backend/app/services/indoor_shield_service.py`, `backend/app/services/ecoroute_service.py`

### 4.2 Grounded AI Copilot with Fail-Closed Validation (Genuinely Implemented)

The copilot does not let the model invent data:

- **FactPack**: Server-built pack of deterministic facts only — no names, coordinates, free text, or health conditions sent to the model.
- **Structured output**: Model must return JSON matching a constrained schema (answer, actions, avoid).
- **Fact reference validation**: All cited fact IDs must exist in the FactPack.
- **Number grounding**: All numeric claims must match FactPack values (within 1% tolerance).
- **Unsafe content stripping**: URLs, HTML, code fences, medical terms removed.
- **Deterministic fallback**: When model is unavailable, rejected, or over budget, a deterministic answer is returned.
- **Citations rebuilt server-side**: Never copied from model output.

**Evidence:** `backend/app/services/copilot_service.py`, `backend/app/integrations/ai/validation.py`, `backend/app/integrations/ai/fallback.py`, `backend/app/domain/facts.py`

### 4.3 Observation vs Forecast Distinction (Genuinely Implemented)

The system explicitly labels data provenance:

- Ground-station observations vs model-based forecasts are never merged.
- Each provider (Open-Meteo, OpenAQ, CPCB) has separate circuit breakers and budgets.
- Stale data is flagged; never presented as current.
- CPCB 2014 AQI method explicitly used.

**Evidence:** `backend/app/services/air_quality_service.py`, `backend/app/domain/aqi.py`

---

## 5. Unverified Competitive Claims

| Claim | Status |
|-------|--------|
| "Industry-first" grounded AI copilot | Not verifiable without market research; several competitors have AI features |
| "Best-in-class accuracy" | No accuracy benchmarks against reference monitors |
| "Real-time" data | Depends on provider freshness; model data is labelled as forecast |

---

## 6. Gaps vs. Competitors

| Gap | Competitor Advantage | Impact |
|-----|---------------------|--------|
| No street-level hyperlocal forecasting | BreezoMeter, Plume | Less precise for micro-locations |
| No pollen / fire / UV tracking | BreezoMeter, IQAir | Narrower environmental scope |
| No owned sensor network | PurpleAir, IQAir | Relies on third-party providers |
| No mobile app (web-only) | IQAir, Plume | Limited mobile accessibility |
| No historical trend analytics | IQAir, BreezoMeter | Limited longitudinal insights |
| No alerting / push notifications | Most competitors | Users must actively check |
| Single household per session | Most competitors support multi-profile | Limits family/household sharing |

---

## 7. Bottom Line

SAANS SAATHI AI is **not trying to out-compete consumer AQI apps on data breadth or mobile presence**. Its differentiation is in **actionability and trustworthiness**:

- Converting AQI into specific actions (routine timing, indoor steps, transport choices)
- Never inventing data (fail-closed AI, sourced factors, provenance labelling)
- Privacy by design (anonymous sessions, no PII to model, consent gating)

This is a credible niche position for an environmental intelligence assistant targeting Indian urban residents who need practical guidance, not just numbers.
