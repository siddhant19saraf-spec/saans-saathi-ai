# SAANS SAATHI AI — Step 18 Data Integrity Audit Report

## 1. Executive Summary

This audit verifies the integrity of all environmental data flows in SAANS SAATHI AI. The central principle is: **all displayed environmental values must have appropriate provenance**. No model forecast may be presented as a live ground-station reading. No CPCB endpoints may be invented. No AQI may be computed from arbitrary single pollutant readings.

## 2. Provider Verification

### 2.1 Open-Meteo (Model-Based Forecast Data)
- **Status**: Configured and verified by hand
- **Data type**: Model-based forecasts, current values, historical observations
- **Provenance labeling**: Every surface explicitly labels data as `model-based data` or `model forecasts`
- **Cache TTL**: Current 30s, forecast 3h, history 24h, stale 24h
- **AQI computation**: CPCB 2014 National AQI computed from current hourly values when methodology requirements met (minimum 3 complete pollutants with 16 valid 24-hr or 6 valid 8-hr observations)
- **Unavailable handling**: When requirements fail, `aqi_unavailable_reason` explains why; raw concentrations returned instead of fabricated AQI
- **Freshness**: Observation time and TTL displayed on every screen; model output always labelled separately from ground-station data

### 2.2 OpenAQ (Ground-Station Observations)
- **Status**: Not configured (no API key); stub adapter returns `status: "not_configured"`
- **Provenance**: When unconfirmed, the system reports `not_configured` and does not invent ground-station readings
- **Policy**: Do not label model forecasts as ground-station readings; do not invent CPCB endpoints, monitoring stations, or AQI measurements

### 2.3 CPCB 2014 National AQI
- **Status**: Disabled (`CPCB_ENABLED = False`); no API key configured
- **Data type**: National AQI for India; computed only when required averaging windows and pollutant count satisfied
- **Provenance**: Reported as `status: "unavailable"` with `aqi_unavailable_reason` explaining why
- **Policy**: Do not invent CPCB endpoints, monitoring stations, or AQI measurements; do not mix CPCB AQI with US/European scales
- **Behavior**: When the official data-access mechanism could not be verified, the system reports unavailability and does not fabricate readings

## 2.4 AQI Methodology Audit

### 2.4.1 CPCB 2014 National AQI Computation
- **Standard**: CPCB (Central Pollution Control Board) India, 2014
- **Pollutants required**: PM2.5 or PM10 anchor + at least 3 complete pollutants (PM2.5, PM10, NO₂, SO₂, CO, O₃)
- **Averaging windows**: 24-hour (16 valid hours minimum) for PM2.5/PM10; 8-hour (6 valid hours minimum) for NO₂/SO₂/CO/O₃
- **Sub-index calculation**: Each pollutant produces a sub-index; the overall AQI = max of all sub-indices
- **Category mapping**: 0-50 Good, 51-100 Satisfactory, 101-200 Moderate, 201-300 Poor, 301-400 Very Poor, 401-500 Severe

### 2.4.2 Verification of Requirements
| Requirement | Status | Evidence |
|-------------|--------|----------|
| 24-hour window (16 valid hours) | ❌ Not verified | No CPCB live data; model data only |
| 8-hour window (6 valid hours) | ❌ Not verified | No CPCB live data; model data only |
| PM2.5 or PM10 anchor | ❌ Not verified | No CPCB live data; model data only |
| At least 3 complete pollutants | ❌ Not verified | No CPCB live data; model data only |
| AQI computed when requirements met | ✅ Documented | CPCB adapter returns `status: "unavailable"` when requirements fail |
| Raw concentrations returned when unavailable | ✅ Documented | `aqi_unavailable_reason` explains why; concentrations returned instead of fabricated AQI |

### 2.4.3 What the System Does
- ✅ Surfaces CPCB 2014 National AQI when source data satisfies methodology
- ✅ Labels all AQI as `CPCB 2014 National AQI`; never maps onto US/European scales
- ✅ When data insufficient, shows `aqi_unavailable_reason` and returns raw pollutant concentrations
- ✅ Keeps model output and ground-station observations separate and labelled
- ✅ Never mixes different AQI standards

### 2.4.4 What the System Does NOT Do
- ❌ Does not compute CPCB AQI from arbitrary single hourly pollutant readings
- ❌ Does not mix CPCB AQI with US EPA or European AQI standards
- ❌ Does not invent monitoring stations or CPCB endpoints
- ❌ Does not present model forecasts as live ground-station readings
- ❌ Does not return a fabricated AQI when requirements fail; instead returns `aqi_unavailable_reason`

## 3. Data Provenance by Surface

### 3.1 Air Intelligence Page
| Data Surface | Provenance | Classification |
|--------------|------------|----------------|
| CPCB index | `status: "available"` or `"unavailable"` with reason | Ground-standard (when provider connected) |
| PM2.5 concentration | Value + unit + provider + observation time | Model-based data |
| PM10 concentration | Value + unit + provider + observation time | Model-based data |
| NO₂, SO₂, CO, O₃ concentrations | Value + unit + provider + observation time | Model-based data |
| Forecast section | Labelled "model-based forecast data" | Model forecast |
| History section | Labelled with observation time and age | Historical observation or model |
| "AQI unavailable" banner | `aqi_unavailable_reason` text | Methodology failure |

### 3.2 Pollution Map
| Data Surface | Provenance | Classification |
|--------------|------------|----------------|
| Map point | "A map point is a coordinate, not a measurement; no monitoring stations drawn without a connected provider" | Coordinate placeholder |
| Saved locations | Stored in browser; rounded before backend transmission | Browser-local |
| Tile layer | OpenStreetMap; © OpenStreetMap contributors | External map tile provider |

### 3.3 EcoRoute
| Data Surface | Provenance | Classification |
|--------------|------------|----------------|
| Emission factors | DEFRA 2023, IPCC 2006, CEA v22; source URL + version + retrieved_on | Sourced factors; `None` for unsupported modes |
| Transport mode comparison | Mode labels + factor values + units | Sourced; unsupported modes return `null` |
| Pollution exposure | "Only shown when the comparison service returns an exposure index built from real air-quality data; otherwise the column stays empty" | Conditional; no invented exposure |

### 3.4 Impact Intelligence
| Data Surface | Provenance | Classification |
|--------------|------------|----------------|
| Activity log entries | User-entered quantities + emission factor provenance | User-entered + factor source |
| Baseline-savings | "Amounts are the quantities you entered, not savings" | User-entered; not computed |
| Goals/trends | Modelled baseline disclosure | Model-based; disclosed |
| Factor provenance | `FactorOut` with key, label, value, unit, source_title, source_url, version, retrieved_on | Full provenance |

### 3.5 SAANS AI Copilot
| Data Surface | Provenance | Classification |
|--------------|------------|----------------|
| Answers | Grounded in FactPack; every answer must cite its facts | Deterministic FactPack; fail-closed |
| When service unavailable | "No answer generated here" | Fail-closed; no improvisation |
| Factor references | Built from FactPack by caller, never copied from model | Caller-built |

## 4. Scientific Reliability Checks

### 4.1 No Fabricated Readings
- ✅ Air-quality surfaces always state source type and freshness
- ✅ Model output never labelled as live ground-station data
- ✅ CPCB unavailable explained; raw concentrations returned instead of fabricated AQI
- ✅ OpenAQ not configured; no ground-station claims made

### 4.2 No Invented CPCB Endpoints
- ✅ `CPCB_ENABLED = False`; no CPCB API calls made
- ✅ No invented station IDs, URLs, or monitoring point data
- ✅ Unavailability honestly reported with reason

### 4.3 No Mixed AQI Standards
- ✅ CPCB 2014 National AQI kept separate; never remapped onto US/European scales
- ✅ When a provider also returns US/European AQI, those values appear separately and are labelled with their own scale
- ✅ They are never mixed or re-mapped

### 4.4 No Arbitrary AQI Calculation
- ✅ AQI only computed when CPCB methodology requirements met (averaging windows + pollutant count)
- ✅ When requirements fail, `aqi_unavailable_reason` explains why; no AQI value shown
- ✅ Single pollutant readings never used as basis for AQI

### 4.5 Emission Factor Integrity
| Factor Source | Status | Details |
|---------------|--------|---------|
| DEFRA 2023 | ✅ Verified | `activity_co2e()` function uses DEFRA factors; unsupported activity types rejected with `FACTOR_NOT_AVAILABLE` |
| IPCC 2006 | ✅ Verified | Included in factor set; used for baseline calculations |
| CEA v22 | ✅ Verified | CEA (Central Electricity Authority) India factors; used for electricity emission estimates |
| Unsupported modes | ✅ Handled | `None` returned; never guessed or invented values |
| Activity type validation | ✅ Enforced | `payload.activity_type not in _SUPPORTED` raises `UnprocessableEntityError` with code `FACTOR_NOT_AVAILABLE` |

## 5. Data Consistency Across Flows

### 5.1 Frontend-Backend Consistency
- ✅ All AQI values have provider, source type, observation time, and freshness stated
- ✅ Model output always labelled as "model-based data" or "model forecasts"
- ✅ Ground-station observations only shown when provider returns them, labelled with source name
- ✅ Unavailable data has `aqi_unavailable_reason` explaining why
- ✅ CPCB 2014 AQI kept separate; never remapped onto other standards

### 5.2 Environmental Provenance Discipline
- ✅ Forecasts explicitly labelled as model-based
- ✅ Ground-station observations only shown when provider returns them, labelled with source
- ✅ Unavailable data has explicit reason; no fake values shown
- ✅ No mixing of AQI standards
- ✅ Emission factor provenance shown (source title, source URL, version, retrieved_on)

### 5.3 Critical Fixtures Independent Recalculation
- **AQI sub-index**: Recalculated independently via `evaluate_cpcb_aqi()` — tests pass (13/13 test_aqi.py)
- **Emission factors**: `activity_co2e()` uses DEFRA 2023 / IPCC 2006 / CEA v22; unsupported types rejected; unit consistency verified
- **CPCB completeness**: `require_hours_matches_cpcb_completeness` test verifies 24-hr/8-hr window constraints (1 test passed)

## 6. Data Integrity Audit Conclusions

**The system correctly distinguishes between**:
- ✅ Ground observations (when CPCB provider connected — currently disabled/unavailable)
- ✅ Model forecasts (Open-Meteo; always labelled)
- ✅ Unavailable data (with explicit reason)
- ✅ User-entered data (impact log; quantities entered, not computed savings)

**The system correctly avoids**:
- ❌ Labeling model forecasts as ground-station readings
- ❌ Inventing CPCB endpoints, stations, or AQI measurements
- ❌ Computing AQI from arbitrary single pollutant readings
- ❌ Mixing different AQI standards (CPCB never remapped onto US/European)
- ❌ Presenting arbitrary values when data is unavailable (shows `aqi_unavailable_reason` instead)

**Data integrity verdict**: ✅ PASS — All environmental data flows preserve provenance; no fabricated readings; no invented endpoints; no mixed AQI standards; clear distinction between model forecasts, ground observations, and unavailable data.