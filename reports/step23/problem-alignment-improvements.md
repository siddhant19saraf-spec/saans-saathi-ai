# SAANS SAATHI AI — Step 23 Problem Statement Alignment Improvements

## 1. Executive Summary

This artifact strengthens SAANS SAATHI AI's alignment with the core problem statement: **Urban air pollution prevents individuals from making informed daily decisions.** The analysis targets the seven modules as the biggest differentiator from ordinary AQI dashboards or chatbots.

**Current Alignment**: ✅ **STRONG** (13/20 score from Step 21 problem-alignment-report.md) — All seven modules address all six barriers from the problem statement. The following improvements strengthen the connections between modules and deepen the contextual decision intelligence.

---

## 2. Module Alignment Strengthening

### 2.1 Air Intelligence → Family Intelligence → SmartRoutine AI Pipeline

| Data Flow Stage | Current | Enhanced | Impact |
|-----------------|---------|----------|--------|
| **Environmental information** | AQI + pollutants displayed with provenance | Add household context auto-injection: "Given your family member with asthma, here's the AQI interpretation" | Personalization depth; competitive differentiator |
| **Validate source and freshness** | CPCB/Open-Meteo provenance labels | Add "freshness advisory": `"Data observed at HH:MM, HH-MM stale"` | User awareness; competitive differentiator |
| **Understand household context** | Health flags optional with consent | Add auto-sensitive-member detection: `_has_sensitive_members()` called from Air Intelligence when generating recommendations | Automatic personalization without extra user steps; competitive differentiator |
| **Evaluate activity constraints** | SmartRoutine scheduler with fixed/flexible windows | Add Air Intelligence → Routine constraint: `"AQI > 150 → outdoor activities postponed"` | Context-aware scheduling; competitive differentiator |
| **Generate deterministic recommendations** | Routine plan with versioned blocks | Add FactPack: `"AQI-driven activity constraints applied"` | Transparency; competitive differentiator |
| **Explain through grounded AI** | FactPack citations from application data | Add explicit sentence: `"Your asthma flag means poor AQI may trigger respiratory recommendations"` | Direct personalization; competitive differentiator |
| **Present actionable decisions** | User makes final call | Add decision summary: `"Based on: AQI=XXX, Asthma flag=Yes, Outdoor activities deferred"` | Full transparency; competitive differentiator |

### 2.2 Air Intelligence → EcoRoute AI → Impact Intelligence Pipeline

| Data Flow Stage | Current | Enhanced | Impact |
|-----------------|---------|----------|--------|
| **Environmental information** | AQI + model data displayed | Add automatic emission factor selection based on AQI season (e.g., winter heating factors) | Seasonal awareness; competitive differentiator |
| **Validate source and freshness** | DEFRA/IPCC/CEA factors with version | Add "factor freshness": `"DEFRA 2023, retrieved YY-MM"` | User awareness; competitive differentiator |
| **Understand household context** | User enters distance + selects modes | Add household size auto-adjustment: `"Per-person emission estimate"` | Personalization; competitive differentiator |
| **Evaluate activity constraints** | User enters distance + selects modes | Add AQI-aware mode selection: `"High AQI → prefer public transport over cycling"` | Context-aware routing; competitive differentiator |
| **Generate deterministic recommendations** | Carbon factors per mode + total | Add "AQI-adjusted recommendation": `"When AQI > 150, consider indoor alternatives"` | Integrated decision support; competitive differentiator |
| **Present actionable decisions** | User chooses based on priorities | Add decision summary: `"Based on: {distance}km, {mode selections}, AQI=XXX"` | Full transparency; competitive differentiator |
| **Savings disclosure** | "Baseline is modelled assumption" | Add: `"Compared to modelled car baseline ({_BASELINE_CAR_KM_PER_DAY} km/day)"` | Consistent with methodology; competitive differentiator |

### 2.3 Air Intelligence → IndoorShield AI → SAANS AI Copilot Pipeline

| Data Flow Stage | Current | Enhanced | Impact |
|-----------------|---------|----------|--------|
| **Environmental information** | AQI displayed; outdoor context in IndoorShield | Add "outdoor AQI influences indoor ventilation decision": `"When AQI > 100, ventilate during low-AQI hours"` | Cross-module context; competitive differentiator |
| **Validate source and freshness** | Outdoor context from AirQualityService | Add "outdoor data freshness": `"Observed at HH:MM, {age_minutes} min ago"` | User awareness; competitive differentiator |
| **Understand household context** | Sensitive members from household profile | Add auto-sensitive-detection in Copilot: `"Given sensitive household members, here are general precautions"` | Automatic personalization; competitive differentiator |
| **Evaluate activity constraints** | 8-item shelter checklist + ventilation guidance | Add AQI-aware ventilation: `"When outdoor AQI good, ventilate; when poor, use air purifier"` | Cross-module intelligence; competitive differentiator |
| **Generate deterministic recommendations** | Action plan with priorities | Add FactPack: `"Outdoor AQI considered in ventilation guidance"` | Transparency; competitive differentiator |
| **Explain through grounded AI** | Deterministic explanation + optional Gemini | Add: `"This explanation considers outdoor AQI={AQI value}, your sensitive members, and indoor sensor status"` | Direct grounded explanation; competitive differentiator |
| **Present actionable decisions** | User follows checklist + ventilation guidance | Add decision summary: `"Based on: AQI=XXX, sensitive members={Yes/No}, indoor sensor status={measured/unavailable}"` | Full transparency; competitive differentiator |

### 2.4 Cross-Module: Problem Statement Alignment Strengthening

| Alignment Criterion | Current | Enhanced | Impact |
|---------------------|---------|----------|--------|
| **Addresses fragmented data** | All 7 modules aggregate data with provenance | Add "data freshness timeline": Each surface shows `observed_at` + `age_minutes` + `stale` flag | Stronger; users understand data age |
| **Addresses technical complexity** | Disclaimers, labelled models, anonymous operation | Add "complexity badge": `"Data from CPCB 2014, Open-Meteo model, DEFRA 2023 — see provenance for each surface"` | User empowerment; competitive differentiator |
| **Addresses lack of personalization** | Household profile + activity preferences | Add "automatic personalization": Health flags + activity constraints → recommendations adjusted without user re-entry | Stronger; reduces user burden |
| **Addresses decision translation** | EcoRoute comparison, SmartRoutine scheduling, EcoRoute exposure | Add "decision flowchart": Visual or text flow showing: AQI → Context → Constraints → Recommendation → Action | User empowerment; competitive differentiator |
| **Addresses privacy concerns** | Anonymous sessions; minimal data collection | Add "privacy control center": Summary of what data is collected, how long retained, deletion controls | Transparency; competitive differentiator |
| **Addresses model-presented-as-live** | CPCB unavailable honestly; model data labelled | Add "source transparency index": Each surface shows `source_type`, `provider`, `observed_at`, `stale` flag + disclaimer | Stronger; users always know data origin |
| **TOTAL** | **13/20** | **Aim for 15/20+** with these enhancements | **Strong → Exceptional** |

---

## 3. Problem Statement Alignment Improvement Artifact

**File**: `reports/step23/problem-alignment-improvements.md` — created as part of Step 23 Phase 7 execution.

**Improvement Summary**:
- 7 module-specific data flow enhancements (Air→Family→Routine, Air→EcoRoute→Impact, Air→IndoorShield→Copilot)
- 6 cross-module alignment criterion enhancements
- Each enhancement connects modules through the problem statement: "Urban air pollution prevents informed daily decisions"
- All enhancements maintain deterministic behavior and provenance discipline
- No fabricated environmental data or unsupported health claims
- Estimated effort: 3-5 developer-days for all improvements
- Projected alignment score improvement: 13/20 → 15/20 (2-point gain from deeper module integration)

**Next steps**: Proceed to Phase 8 — AI Engineering Evaluation (ai-integration-evaluation.md).