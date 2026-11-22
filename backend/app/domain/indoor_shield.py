"""Deterministic IndoorShield recommendation engine.

The engine turns a completed home assessment, validated indoor sensor samples,
and outdoor air-quality context into prioritised, explainable household actions.

It deliberately does not:

* diagnose mould, asthma, chemical contamination or any medical condition;
* present an outdoor concentration as an indoor measurement;
* treat a low-cost sensor reading as certified regulatory monitoring;
* promise pollutant removal or a quantified health improvement.

Priority is a transparent score, not a measurement. Rules carry a base score;
repeat/frequent sources and sensitive occupants can raise it. Scores at or above
300 are high priority, 190-299 medium, and below 190 low.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

ENGINE_VERSION = "indoor-shield-1.0.0"

WHO_PM25_24H = 15.0
WHO_PM10_24H = 45.0
WHO_CO_24H_MG_M3 = 4.0
CO2_VENTILATION_INDICATOR_PPM = 1000.0
HUMIDITY_LOW_PERCENT = 30.0
HUMIDITY_HIGH_PERCENT = 60.0
TARGET_AIR_CHANGES = 5.0

PRIORITY_HIGH = 300
PRIORITY_MEDIUM = 190

WHO_AQG_2021 = (
    "WHO global air quality guidelines (2021): 24-hour PM2.5 guideline "
    "15 µg/m³, PM10 45 µg/m³ and CO 4 mg/m³."
)
WHO_HOUSEHOLD = (
    "WHO household air pollution guidance: cleaner fuels, improved stoves and "
    "ventilation reduce exposure to household combustion smoke."
)
EPA_SOURCE_CONTROL = (
    "US EPA indoor air guidance: source control, ventilation and filtration, "
    "in that order of preference."
)
EPA_MOISTURE = (
    "US EPA moisture and mould guidance: fix leaks, dry damp materials and "
    "reduce moisture; do not infer a diagnosis from a questionnaire."
)
ASHRAE_VENTILATION = (
    "ASHRAE 62.1/62.2 ventilation guidance: use local exhaust at cooking "
    "appliances and maintain adequate outdoor-air ventilation."
)
MANUFACTURER_FILTER = "Device manufacturer's filter-maintenance instructions."


@dataclass(frozen=True, slots=True)
class RoomSnapshot:
    name: str
    room_type: str
    area_m2: float
    ceiling_m: float
    ventilation: str
    windows_count: int
    has_purifier: bool
    purifier_cadr: int | None
    dampness: str


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    code: str
    frequency: str


@dataclass(frozen=True, slots=True)
class SensorSnapshot:
    pollutant: str
    value: float
    unit: str
    measured_at: datetime
    calibration_status: str


@dataclass(frozen=True, slots=True)
class OutdoorSnapshot:
    available: bool
    provider: str | None = None
    observed_at: datetime | None = None
    stale: bool = False
    pm2_5: float | None = None
    pm10: float | None = None
    cpcb_aqi: int | None = None
    forecast_available: bool = False
    forecast_min_pm2_5: float | None = None
    forecast_min_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class AssessmentSnapshot:
    rooms: tuple[RoomSnapshot, ...]
    sources: tuple[SourceSnapshot, ...]
    cooking_fuel: str
    cooking_location: str
    cooking_exhaust: bool
    cleaning_frequency: str
    sensor_available: bool
    sensitive_members: bool = False


@dataclass(frozen=True, slots=True)
class RecommendationDraft:
    rule_id: str
    category: str
    title: str
    description: str
    issue: str
    action: str
    priority_score: int
    evidence: str
    expected_benefit: str
    limitations: str
    frequency: str
    due_at: datetime | None = None

    @property
    def priority(self) -> str:
        if self.priority_score >= PRIORITY_HIGH:
            return "high"
        if self.priority_score >= PRIORITY_MEDIUM:
            return "medium"
        return "low"


@dataclass(frozen=True, slots=True)
class PlanDraft:
    recommendations: tuple[RecommendationDraft, ...]
    summary: str
    confidence: str
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "engine_version": ENGINE_VERSION,
            "summary": self.summary,
            "confidence": self.confidence,
            "assumptions": list(self.assumptions),
            "limitations": list(self.limitations),
            "recommendations": [
                {
                    "rule_id": item.rule_id,
                    "category": item.category,
                    "title": item.title,
                    "description": item.description,
                    "issue": item.issue,
                    "action": item.action,
                    "priority": item.priority,
                    "priority_score": item.priority_score,
                    "evidence": item.evidence,
                    "expected_benefit": item.expected_benefit,
                    "limitations": item.limitations,
                    "frequency": item.frequency,
                    "due_at": item.due_at.isoformat() if item.due_at else None,
                }
                for item in self.recommendations
            ],
        }


_FREQUENCY_BOOST = {
    "occasional": 0,
    "weekly": 5,
    "daily": 20,
    "frequent": 30,
}

_SOURCE_RULES: dict[str, RecommendationDraft] = {
    "biomass_cooking": RecommendationDraft(
        rule_id="IND-SRC-SOLID-FUEL",
        category="cooking",
        title="Move solid-fuel cooking outdoors or switch to a cleaner fuel",
        description=(
            "Wood, dung, crop residue and charcoal produce very high indoor "
            "particle concentrations. Prefer a clean fuel and outdoor cooking "
            "where that is practical."
        ),
        issue="Solid-fuel or biomass cooking was reported.",
        action=(
            "Use the cleanest available fuel, cook outdoors when possible, and "
            "keep children away from the cooking area while it is in use."
        ),
        priority_score=360,
        evidence=WHO_HOUSEHOLD,
        expected_benefit=(
            "May substantially reduce indoor smoke exposure when a cleaner fuel "
            "or outdoor cooking is consistently used."
        ),
        limitations=(
            "Fuel switching depends on cost, supply and safety; this app cannot "
            "measure the change in your home."
        ),
        frequency="daily",
    ),
    "gas_stove": RecommendationDraft(
        rule_id="IND-COOK-GAS",
        category="cooking",
        title="Use an effective hood or exhaust while the gas stove is on",
        description=(
            "Gas combustion and cooking fumes add particles and nitrogen dioxide. "
            "A hood vented outdoors, or a nearby exhaust fan, removes more than an "
            "open window alone."
        ),
        issue="Gas-stove cooking was reported.",
        action=(
            "Run the exhaust or hood at the start of cooking and for several "
            "minutes afterwards. Open a window only when outdoor air is not "
            "especially polluted."
        ),
        priority_score=280,
        evidence=ASHRAE_VENTILATION,
        expected_benefit=(
            "May reduce cooking-related particles and combustion gases at the "
            "stove, particularly when the exhaust vents outdoors."
        ),
        limitations=(
            "Recirculating hoods without outdoor exhaust provide limited "
            "particle removal. Effectiveness depends on capture and airflow."
        ),
        frequency="daily",
    ),
    "cooking_fumes": RecommendationDraft(
        rule_id="IND-COOK-VENT",
        category="cooking",
        title="Ventilate the kitchen during and after cooking",
        description=(
            "Frying and high-heat cooking create fine particles and odours. "
            "Local exhaust is the most direct control."
        ),
        issue="Cooking fumes were reported as an indoor source.",
        action=(
            "Use the exhaust fan or open a window while cooking and for a short "
            "period afterwards. Wipe cooking surfaces when they have cooled."
        ),
        priority_score=250,
        evidence=EPA_SOURCE_CONTROL,
        expected_benefit="May lower cooking-related particle and odour levels.",
        limitations=(
            "Opening windows can also let outdoor particles in when outdoor "
            "pollution is high."
        ),
        frequency="daily",
    ),
    "candles_incense": RecommendationDraft(
        rule_id="IND-SRC-CANDLES",
        category="cooking",
        title="Reduce candles, incense and other indoor burning",
        description=(
            "Candles and incense are small combustion sources that can raise "
            "indoor particles, especially in a closed room."
        ),
        issue="Candles or incense were reported.",
        action=(
            "Burn less often, avoid enclosed rooms, and ventilate afterwards. "
            "Choose battery or electric alternatives where practical."
        ),
        priority_score=230,
        evidence=EPA_SOURCE_CONTROL,
        expected_benefit="May reduce a recurring indoor particle source.",
        limitations=(
            "Occasional use in a well-ventilated room is different from daily use "
            "in a closed bedroom; this app does not estimate the dose."
        ),
        frequency="weekly",
    ),
    "tobacco_smoke": RecommendationDraft(
        rule_id="IND-SRC-TOBACCO",
        category="cooking",
        title="Keep tobacco smoke out of the home",
        description=(
            "Tobacco smoke contains fine particles and other harmful substances. "
            "Opening a window does not reliably remove it from an indoor space."
        ),
        issue="Indoor tobacco smoke was reported.",
        action=(
            "Smoke outdoors, away from doors and windows, and avoid smoking in "
            "rooms used by children or other household members."
        ),
        priority_score=390,
        evidence=WHO_HOUSEHOLD,
        expected_benefit=(
            "A smoke-free home is the most reliable way to reduce second-hand "
            "smoke exposure."
        ),
        limitations=(
            "This is general household guidance, not medical advice or a "
            "measurement of exposure."
        ),
        frequency="daily",
    ),
    "indoor_burning": RecommendationDraft(
        rule_id="IND-SRC-BURNING",
        category="cooking",
        title="Stop indoor burning of waste or fuel",
        description=(
            "Burning paper, plastic, wood or other material indoors can release "
            "large amounts of smoke and fine particles."
        ),
        issue="Indoor burning was reported.",
        action=(
            "Move burning outdoors, never burn plastic or treated material, and "
            "follow local waste rules."
        ),
        priority_score=380,
        evidence=WHO_HOUSEHOLD,
        expected_benefit="Removes a strong, avoidable indoor particle source.",
        limitations=(
            "If burning is a necessity, the priority is ventilation and keeping "
            "the burn area separated from living spaces."
        ),
        frequency="daily",
    ),
    "cleaning_products": RecommendationDraft(
        rule_id="IND-SRC-CLEANING",
        category="cleaning",
        title="Use cleaning products with ventilation and follow the label",
        description=(
            "Some cleaners release volatile chemicals and fine droplets. Mixing "
            "products can create dangerous gases."
        ),
        issue="Cleaning-product use was reported as a source.",
        action=(
            "Never mix products, follow label directions and ventilate the room. "
            "Keep children and pets away while surfaces dry."
        ),
        priority_score=240,
        evidence=EPA_SOURCE_CONTROL,
        expected_benefit="May reduce avoidable chemical exposure during cleaning.",
        limitations=(
            "This app does not identify or measure specific chemicals in the home."
        ),
        frequency="weekly",
    ),
    "aerosol_sprays": RecommendationDraft(
        rule_id="IND-SRC-AEROSOL",
        category="cleaning",
        title="Reduce aerosol sprays and use pump or wipe alternatives",
        description=(
            "Aerosol sprays produce fine droplets that can remain airborne and "
            "irritate the eyes, nose or throat."
        ),
        issue="Aerosol spray use was reported.",
        action=(
            "Prefer a pump, cloth or targeted application, and ventilate the room "
            "when a spray is necessary."
        ),
        priority_score=240,
        evidence=EPA_SOURCE_CONTROL,
        expected_benefit="May reduce airborne droplets and a recurring source.",
        limitations=(
            "Product contents differ; follow the manufacturer's safety instructions."
        ),
        frequency="weekly",
    ),
    "paints_solvents": RecommendationDraft(
        rule_id="IND-SRC-PAINT",
        category="cleaning",
        title="Ventilate when using paints, solvents or adhesives",
        description=(
            "Paints, solvents and adhesives can release volatile organic compounds "
            "after application."
        ),
        issue="Paints or solvents were reported.",
        action=(
            "Follow the product label, ventilate the work area, and keep occupants "
            "away until the product has cured as directed."
        ),
        priority_score=300,
        evidence=EPA_SOURCE_CONTROL,
        expected_benefit=(
            "May reduce exposure to volatile chemicals during and after work."
        ),
        limitations=(
            "The app does not measure VOC concentrations or assess chemical "
            "toxicity; a qualified professional may be needed for large projects."
        ),
        frequency="once",
    ),
    "renovation_materials": RecommendationDraft(
        rule_id="IND-SRC-RENOVATION",
        category="cleaning",
        title="Isolate renovation dust and ventilate after the work",
        description=(
            "Sanding, demolition and new furnishings can add dust and chemical "
            "emissions over days or weeks."
        ),
        issue="Renovation or new furnishing materials were reported.",
        action=(
            "Use dust barriers, HEPA vacuuming where available, and ventilate the "
            "area. Follow product off-gassing instructions."
        ),
        priority_score=300,
        evidence=EPA_SOURCE_CONTROL,
        expected_benefit="May reduce renovation dust spreading into living areas.",
        limitations=(
            "Containment and safe work practices matter more than any single "
            "ventilation step; this app does not inspect the work area."
        ),
        frequency="weekly",
    ),
    "dust": RecommendationDraft(
        rule_id="IND-SRC-DUST",
        category="dust",
        title="Damp-wipe and reduce dust accumulation",
        description=(
            "Settled dust can be resuspended by walking, cleaning or air movement. "
            "Damp methods capture it instead of lifting it into the air."
        ),
        issue="Dust was reported as an indoor source.",
        action=(
            "Damp-wipe hard surfaces, use entrance mats, and vacuum with a suitable "
            "filter where available."
        ),
        priority_score=220,
        evidence=EPA_SOURCE_CONTROL,
        expected_benefit="May reduce settled dust becoming airborne again.",
        limitations=(
            "This does not remove the original source, and the app cannot measure "
            "the resulting particle change."
        ),
        frequency="weekly",
    ),
    "outdoor_infiltration": RecommendationDraft(
        rule_id="IND-SRC-INFILTRATION",
        category="outdoor_pollution",
        title="Check outdoor conditions before ventilating",
        description=(
            "Outdoor particles can enter through open windows, doors and gaps. "
            "Indoor concentration is not determined by outdoor concentration alone."
        ),
        issue="Outdoor pollution infiltration was identified as a concern.",
        action=(
            "Compare the outdoor context before opening windows for long periods, "
            "and use short ventilation when outdoor PM2.5 is lower."
        ),
        priority_score=250,
        evidence=EPA_SOURCE_CONTROL,
        expected_benefit="May reduce unnecessary outdoor particle entry.",
        limitations=(
            "Building tightness, wind, indoor sources and filtration all affect "
            "indoor air; this app does not model your building."
        ),
        frequency="daily",
    ),
    "poor_ventilation": RecommendationDraft(
        rule_id="IND-VENT-POOR",
        category="ventilation",
        title="Establish a deliberate ventilation routine",
        description=(
            "Without regular air exchange, indoor pollutants and moisture can "
            "accumulate."
        ),
        issue="Poor ventilation was reported.",
        action=(
            "Use short cross-ventilation when outdoor air is acceptable, run "
            "local exhaust at cooking and in bathrooms, and keep vents unblocked."
        ),
        priority_score=260,
        evidence=ASHRAE_VENTILATION,
        expected_benefit="May reduce accumulated indoor pollutants and moisture.",
        limitations=(
            "Opening windows during outdoor pollution peaks can increase indoor "
            "particles; check the outdoor context first."
        ),
        frequency="daily",
    ),
    "dampness": RecommendationDraft(
        rule_id="IND-MOISTURE",
        category="humidity",
        title="Find and dry persistent damp areas",
        description=(
            "Damp surfaces and leaks can support mould growth. The first step is "
            "to remove the moisture source, not to cover it up."
        ),
        issue="Dampness was reported.",
        action=(
            "Fix leaks, dry wet materials within 24-48 hours where practical, and "
            "improve ventilation in bathrooms and kitchens."
        ),
        priority_score=290,
        evidence=EPA_MOISTURE,
        expected_benefit="May reduce conditions that allow mould and dampness.",
        limitations=(
            "This app does not diagnose mould or hidden moisture. Persistent "
            "dampness may need a qualified building or environmental professional."
        ),
        frequency="weekly",
    ),
    "mold_risk": RecommendationDraft(
        rule_id="IND-MOLD-RISK",
        category="humidity",
        title="Inspect possible damp or mould conditions without guessing",
        description=(
            "Visible or persistent dampness should be investigated. A "
            "questionnaire cannot diagnose mould or a health effect."
        ),
        issue="A possible damp or mould condition was reported.",
        action=(
            "Look for leaks and visible growth, dry the area, and arrange a "
            "professional inspection if dampness persists."
        ),
        priority_score=330,
        evidence=EPA_MOISTURE,
        expected_benefit=(
            "May address the moisture conditions associated with mould growth."
        ),
        limitations=(
            "This is not a mould diagnosis or a health assessment. Some materials "
            "need professional removal."
        ),
        frequency="weekly",
    ),
    "other": RecommendationDraft(
        rule_id="IND-SRC-OTHER",
        category="general",
        title="Describe and inspect the remaining indoor source",
        description=(
            "An indoor source was reported under 'other'. Identifying the exact "
            "activity or material helps choose a targeted control."
        ),
        issue="An unclassified indoor source was reported.",
        action=(
            "Note when the source occurs and what it smells or looks like, then "
            "address the source before relying on ventilation or a purifier."
        ),
        priority_score=140,
        evidence=EPA_SOURCE_CONTROL,
        expected_benefit="May make later guidance more specific.",
        limitations=(
            "The app cannot identify an unknown source from a free-text note."
        ),
        frequency="once",
    ),
}


def _priority_score(base: int, *, frequency: str | None, sensitive: bool) -> int:
    score = base
    if frequency is not None:
        score += _FREQUENCY_BOOST.get(frequency, 0)
    if sensitive and base >= 250:
        score += 15
    return score


def _add(
    rules: dict[str, RecommendationDraft],
    recommendation: RecommendationDraft,
) -> None:
    existing = rules.get(recommendation.rule_id)
    if existing is None or recommendation.priority_score > existing.priority_score:
        rules[recommendation.rule_id] = recommendation


def _source_recommendation(
    source: SourceSnapshot, *, sensitive: bool
) -> RecommendationDraft | None:
    template = _SOURCE_RULES.get(source.code)
    if template is None:
        return None
    return RecommendationDraft(
        rule_id=template.rule_id,
        category=template.category,
        title=template.title,
        description=template.description,
        issue=template.issue,
        action=template.action,
        priority_score=_priority_score(
            template.priority_score,
            frequency=source.frequency,
            sensitive=sensitive,
        ),
        evidence=template.evidence,
        expected_benefit=template.expected_benefit,
        limitations=template.limitations,
        frequency=template.frequency,
    )


def _sensor_rule(sample: SensorSnapshot) -> RecommendationDraft | None:
    calibration_note = (
        " The device is not independently calibrated; treat the reading as an "
        "indicator, not certified monitoring."
        if sample.calibration_status != "verified"
        else ""
    )
    if sample.pollutant == "pm2_5" and sample.value > WHO_PM25_24H:
        return RecommendationDraft(
            rule_id="IND-SENSOR-PM25",
            category="filtration",
            title="Respond to the elevated indoor PM2.5 reading",
            description=(
                f"The latest PM2.5 reading is {sample.value:g} µg/m³, above the "
                f"WHO 24-hour guideline value of {WHO_PM25_24H:g} µg/m³. A single "
                "reading is not a 24-hour average."
            ),
            issue="The low-cost sensor reported PM2.5 above the WHO guideline value.",
            action=(
                "Check for a source such as cooking or smoking, increase "
                "ventilation only if outdoor air is suitable, and use filtration "
                "if available."
            ),
            priority_score=330 if sample.value > 35 else 300,
            evidence=WHO_AQG_2021,
            expected_benefit=(
                "May reduce the indoor particle level when the source and "
                "ventilation route are addressed."
            ),
            limitations=(
                "Low-cost sensors are not equivalent to certified regulatory "
                "monitors, and one reading does not establish a daily average."
                + calibration_note
            ),
            frequency="daily",
        )
    if sample.pollutant == "pm10" and sample.value > WHO_PM10_24H:
        return RecommendationDraft(
            rule_id="IND-SENSOR-PM10",
            category="dust",
            title="Investigate the elevated indoor PM10 reading",
            description=(
                f"The latest PM10 reading is {sample.value:g} µg/m³, above the "
                f"WHO 24-hour guideline value of {WHO_PM10_24H:g} µg/m³."
            ),
            issue="The sensor reported PM10 above the WHO guideline value.",
            action=(
                "Check for dust, renovation work or tracked-in soil, clean with "
                "damp methods and ventilate when outdoor conditions are suitable."
            ),
            priority_score=260,
            evidence=WHO_AQG_2021,
            expected_benefit="May reduce an identifiable coarse-particle source.",
            limitations=(
                "A low-cost PM10 reading is an indicator and may include water "
                "droplets or other particles." + calibration_note
            ),
            frequency="daily",
        )
    if sample.pollutant == "co2" and sample.value > CO2_VENTILATION_INDICATOR_PPM:
        return RecommendationDraft(
            rule_id="IND-SENSOR-CO2",
            category="ventilation",
            title="Increase ventilation after the elevated CO2 reading",
            description=(
                f"The latest CO2 reading is {sample.value:g} ppm, above the "
                "common 1,000 ppm ventilation indicator. It is a ventilation "
                "signal, not a health diagnosis."
            ),
            issue="The sensor reported a high CO2 level.",
            action=(
                "Open a window briefly or improve mechanical ventilation, then "
                "re-check the reading. Reduce occupancy in a small closed room if "
                "ventilation cannot be improved."
            ),
            priority_score=250,
            evidence=ASHRAE_VENTILATION,
            expected_benefit="May improve fresh-air exchange and reduce CO2 build-up.",
            limitations=(
                "CO2 is used here as a ventilation indicator, not as a direct "
                "measure of all indoor pollutants."
            ),
            frequency="daily",
        )
    if sample.pollutant == "co" and sample.value > WHO_CO_24H_MG_M3:
        return RecommendationDraft(
            rule_id="IND-SENSOR-CO",
            category="cooking",
            title="Treat the elevated carbon-monoxide reading as urgent",
            description=(
                f"The latest CO reading is {sample.value:g} mg/m³, above the WHO "
                "24-hour guideline value. Carbon monoxide can be life-threatening."
            ),
            issue="The sensor reported carbon monoxide above the guideline value.",
            action=(
                "Stop combustion sources, ventilate if it is safe to do so, leave "
                "the area if anyone has symptoms, and seek emergency help. Do not "
                "ignore a persistent CO alarm."
            ),
            priority_score=400,
            evidence=WHO_AQG_2021,
            expected_benefit=(
                "Removing the source and leaving the area reduces immediate "
                "carbon-monoxide exposure."
            ),
            limitations=(
                "This app cannot confirm a CO leak. Use a certified alarm and "
                "emergency services when exposure is suspected."
            ),
            frequency="once",
        )
    if sample.pollutant == "tvoc":
        return RecommendationDraft(
            rule_id="IND-SENSOR-VOC",
            category="cleaning",
            title="Ventilate and look for a VOC source",
            description=(
                f"The latest TVOC reading is {sample.value:g} {sample.unit}. There "
                "is no single health-based TVOC threshold used here."
            ),
            issue="The sensor reported a TVOC reading that needs investigation.",
            action=(
                "Check for recent painting, cleaning, new furniture or solvents, "
                "ventilate the room and follow product labels."
            ),
            priority_score=210,
            evidence=EPA_SOURCE_CONTROL,
            expected_benefit="May reduce a source of odours and volatile chemicals.",
            limitations=(
                "TVOC sensors vary in selectivity and calibration; do not interpret "
                "one number as a health risk." + calibration_note
            ),
            frequency="weekly",
        )
    if sample.pollutant == "humidity" and (
        sample.value < HUMIDITY_LOW_PERCENT or sample.value > HUMIDITY_HIGH_PERCENT
    ):
        return RecommendationDraft(
            rule_id="IND-SENSOR-HUMIDITY",
            category="humidity",
            title="Bring indoor humidity into a comfortable range",
            description=(
                f"The latest relative-humidity reading is {sample.value:g}%. Very "
                "dry or persistently damp air can affect comfort and materials."
            ),
            issue="The humidity reading is outside the general comfort range.",
            action=(
                "Ventilate bathrooms and kitchens, fix leaks, and use a "
                "dehumidifier or humidifier only as appropriate for the cause."
            ),
            priority_score=200,
            evidence=EPA_MOISTURE,
            expected_benefit="May improve comfort and reduce moisture conditions.",
            limitations=(
                "Comfort ranges vary by season and person. This is not a mould "
                "diagnosis or a complete moisture assessment."
            ),
            frequency="weekly",
        )
    return None


def _outdoor_rules(
    outdoor: OutdoorSnapshot,
    *,
    has_windows: bool,
    has_purifier: bool,
    sensitive: bool,
) -> list[RecommendationDraft]:
    if not outdoor.available:
        return []
    if outdoor.stale:
        # A stale observation is shown for transparency but is never used to
        # time ventilation or to claim that outdoor particles are elevated.
        return [
            RecommendationDraft(
                rule_id="IND-OUTDOOR-STALE",
                category="outdoor_pollution",
                title="Refresh the outdoor reading before changing ventilation",
                description=(
                    "The saved outdoor observation is older than the freshness "
                    "limit. Its value may no longer describe current conditions."
                ),
                issue="The outdoor observation is stale.",
                action=(
                    "Refresh the outdoor air-quality context, then decide whether "
                    "to ventilate. Keep local exhaust running for cooking in the "
                    "meantime."
                ),
                priority_score=180,
                evidence=EPA_SOURCE_CONTROL,
                expected_benefit="Avoids acting on an out-of-date outdoor reading.",
                limitations=(
                    "No current outdoor measurement is available to this app. "
                    "Indoor sources still need source control."
                ),
                frequency="once",
            )
        ]
    rules: list[RecommendationDraft] = []
    if outdoor.pm2_5 is not None and outdoor.pm2_5 > WHO_PM25_24H:
        score = 330 if outdoor.pm2_5 > 35 else 300
        if sensitive:
            score += 15
        rules.append(
            RecommendationDraft(
                rule_id="IND-OUTDOOR-PEAK",
                category="outdoor_pollution",
                title="Keep windows closed during the outdoor pollution peak",
                description=(
                    f"Outdoor PM2.5 is {outdoor.pm2_5:g} µg/m³ in the available "
                    "context, above the WHO 24-hour guideline value. Outdoor air "
                    "does not determine indoor concentration, but open windows can "
                    "increase particle entry."
                ),
                issue="Outdoor PM2.5 is above the WHO guideline value.",
                action=(
                    "Keep windows closed during peaks, use local exhaust for "
                    "cooking, and rely on filtration if you have a suitable purifier."
                ),
                priority_score=score,
                evidence=EPA_SOURCE_CONTROL,
                expected_benefit=(
                    "May reduce particle entry while outdoor concentrations are high."
                ),
                limitations=(
                    "Closing windows can trap indoor moisture and other pollutants. "
                    "This is not a measurement of your indoor air."
                ),
                frequency="daily",
            )
        )
    if outdoor.forecast_available and outdoor.forecast_min_pm2_5 is not None:
        if outdoor.forecast_min_pm2_5 <= WHO_PM25_24H:
            rules.append(
                RecommendationDraft(
                    rule_id="IND-OUTDOOR-VENTILATE",
                    category="ventilation",
                    title="Use the lower-forecast outdoor window for short ventilation",
                    description=(
                        "The forecast's lowest PM2.5 hour is shown in the outdoor "
                        "context. It is a relative low point, not a guarantee that "
                        "the air is safe."
                    ),
                    issue="A lower-forecast ventilation window is available.",
                    action=(
                        "Open windows briefly around the lower-forecast hour, then "
                        "close them. Re-check the outdoor context before a longer "
                        "exchange."
                    ),
                    priority_score=200 + (15 if sensitive else 0),
                    evidence=EPA_SOURCE_CONTROL,
                    expected_benefit=(
                        "May exchange indoor air while outdoor particle levels are "
                        "relatively lower."
                    ),
                    limitations=(
                        "Forecast values are modelled and may differ from "
                        "street-level conditions. Indoor sources still matter."
                    ),
                    frequency="daily",
                    due_at=outdoor.forecast_min_at,
                )
            )
        else:
            rules.append(
                RecommendationDraft(
                    rule_id="IND-OUTDOOR-NO-CLEAN-WINDOW",
                    category="outdoor_pollution",
                    title="Do not rely on window ventilation at the forecast low point",
                    description=(
                        "The lowest forecast PM2.5 in the available horizon remains "
                        "above the WHO 24-hour guideline value. Opening windows may "
                        "add particles."
                    ),
                    issue="No low-forecast window was below the WHO guideline value.",
                    action=(
                        "Keep windows closed for long periods, use local exhaust at "
                        "cooking, and use a suitable purifier if available. Air the "
                        "home briefly if moisture or odours build up."
                    ),
                    priority_score=280 + (15 if sensitive else 0),
                    evidence=EPA_SOURCE_CONTROL,
                    expected_benefit=(
                        "May avoid adding outdoor particles during a period with no "
                        "clear low point."
                    ),
                    limitations=(
                        "Indoor air can still need ventilation; this app does not "
                        "measure indoor CO2 or moisture."
                    ),
                    frequency="daily",
                )
            )
    if not outdoor.forecast_available and not has_purifier:
        rules.append(
            RecommendationDraft(
                rule_id="IND-OUTDOOR-DATA-GAP",
                category="outdoor_pollution",
                title="Check current outdoor data before changing ventilation",
                description=(
                    "The outdoor observation is stale or the forecast is unavailable. "
                    "Do not treat the last value as current."
                ),
                issue="Outdoor context is incomplete or stale.",
                action=(
                    "Refresh the outdoor reading before opening windows for a long "
                    "period or deciding that filtration is unnecessary."
                ),
                priority_score=170,
                evidence=EPA_SOURCE_CONTROL,
                expected_benefit="Avoids acting on an out-of-date outdoor reading.",
                limitations="No current outdoor measurement is available to this app.",
                frequency="once",
            )
        )
    if has_windows and has_purifier and outdoor.pm2_5 is not None:
        rules.append(
            RecommendationDraft(
                rule_id="IND-FILTER-USE",
                category="filtration",
                title="Use the purifier during the outdoor peak",
                description=(
                    "A purifier can reduce indoor particles when its clean-air "
                    "delivery rate is appropriate for the room and its filter is "
                    "maintained."
                ),
                issue="Outdoor particle levels are elevated and a purifier is available.",
                action=(
                    "Run the purifier in the room you use most, keep doors and "
                    "windows closed where practical, and follow the manufacturer's "
                    "filter schedule."
                ),
                priority_score=220,
                evidence=EPA_SOURCE_CONTROL,
                expected_benefit="May reduce indoor particles when correctly sized and maintained.",
                limitations=(
                    "A purifier does not remove gases or carbon monoxide and cannot "
                    "compensate for an uncontrolled source."
                ),
                frequency="daily",
            )
        )
    return rules


def recommend(
    assessment: AssessmentSnapshot,
    sensors: tuple[SensorSnapshot, ...],
    outdoor: OutdoorSnapshot,
) -> PlanDraft:
    """Return a deterministic, ordered recommendation set."""
    rules: dict[str, RecommendationDraft] = {}
    sensitive = assessment.sensitive_members

    for source in assessment.sources:
        recommendation = _source_recommendation(source, sensitive=sensitive)
        if recommendation is not None:
            _add(rules, recommendation)

    for room in assessment.rooms:
        if room.dampness in {"occasional", "persistent"}:
            score = 320 if room.dampness == "persistent" else 280
            if sensitive:
                score += 15
            _add(
                rules,
                RecommendationDraft(
                    rule_id="IND-ROOM-MOISTURE",
                    category="humidity",
                    title=f"Dry the damp area in the {room.name}",
                    description=(
                        "Dampness was reported in this room. Removing the moisture "
                        "source is the first step; do not rely on fragrance or "
                        "covering the area."
                    ),
                    issue=f"Dampness was reported in {room.name}.",
                    action=(
                        "Find and fix the leak or moisture path, dry the room and "
                        "ventilate it. Seek professional help if dampness persists."
                    ),
                    priority_score=score,
                    evidence=EPA_MOISTURE,
                    expected_benefit="May reduce conditions that support mould growth.",
                    limitations=(
                        "A questionnaire cannot confirm mould or hidden moisture."
                    ),
                    frequency="weekly",
                ),
            )
        if room.ventilation == "none" and not room.windows_count:
            _add(
                rules,
                RecommendationDraft(
                    rule_id="IND-ROOM-NO-VENTILATION",
                    category="ventilation",
                    title=f"Create a ventilation path for the {room.name}",
                    description=(
                        "No window, exhaust or mechanical ventilation was reported "
                        "for this room."
                    ),
                    issue=f"{room.name} has no reported ventilation path.",
                    action=(
                        "Keep doors open where safe, use a fan to move air, and "
                        "arrange a suitable exhaust or ventilation opening."
                    ),
                    priority_score=270,
                    evidence=ASHRAE_VENTILATION,
                    expected_benefit="May reduce accumulated pollutants and moisture.",
                    limitations=(
                        "A fan alone does not remove pollutants unless it moves air "
                        "to an exhaust path."
                    ),
                    frequency="weekly",
                ),
            )
        if room.has_purifier and room.purifier_cadr is not None:
            volume = room.area_m2 * room.ceiling_m
            target = int(round(volume * TARGET_AIR_CHANGES / 10.0) * 10)
            if room.purifier_cadr < target:
                _add(
                    rules,
                    RecommendationDraft(
                        rule_id=f"IND-FILTER-SIZING-{room.name.lower().replace(' ', '-')}",
                        category="filtration",
                        title=f"Match the purifier to the {room.name}",
                        description=(
                            f"The room is about {volume:.0f} m³. A clean-air "
                            f"delivery rate of roughly {target} m³/h is about five "
                            "air changes per hour; the saved setting is "
                            f"{room.purifier_cadr} m³/h."
                        ),
                        issue=f"The saved purifier CADR is below the sizing guide for {room.name}.",
                        action=(
                            "Use a larger unit or a lower-clearance setting only as "
                            "the manufacturer allows, and keep the filter clean."
                        ),
                        priority_score=210,
                        evidence=EPA_SOURCE_CONTROL,
                        expected_benefit="May improve particle removal if the room is closed.",
                        limitations=(
                            "Five air changes per hour is a planning guide, not a "
                            "guarantee. Real performance depends on the device, "
                            "filter and room leakage."
                        ),
                        frequency="once",
                    ),
                )
        if room.has_purifier:
            _add(
                rules,
                RecommendationDraft(
                    rule_id="IND-FILTER-MAINT",
                    category="filtration",
                    title="Maintain the purifier filter on schedule",
                    description=(
                        "A loaded filter reduces airflow. Follow the device "
                        "manufacturer's interval rather than an invented one."
                    ),
                    issue="A purifier is available and needs maintenance.",
                    action=(
                        "Check the filter indicator, clean the pre-filter if the "
                        "manufacturer allows, and replace the filter when due."
                    ),
                    priority_score=180,
                    evidence=MANUFACTURER_FILTER,
                    expected_benefit="Helps the device keep its intended airflow.",
                    limitations=(
                        "Filter life depends on use, outdoor particles and the model."
                    ),
                    frequency="monthly",
                ),
            )

    fuel = assessment.cooking_fuel
    if fuel in {"lpg", "png", "biomass", "mixed"} and (not assessment.cooking_exhaust):
        _add(
            rules,
            RecommendationDraft(
                rule_id="IND-COOK-EXHAUST",
                category="cooking",
                title="Use an outdoor-venting exhaust while cooking",
                description=(
                    "Cooking with gas or solid fuel without local exhaust adds "
                    "particles and combustion gases to the kitchen."
                ),
                issue="Cooking occurs indoors without reported local exhaust.",
                action=(
                    "Run an exhaust hood or fan that vents outdoors during "
                    "cooking on the stove and for several minutes afterwards."
                ),
                priority_score=300 if fuel in {"biomass", "mixed"} else 280,
                evidence=ASHRAE_VENTILATION,
                expected_benefit="May reduce cooking-related pollutants near the stove.",
                limitations=(
                    "A recirculating filter is not equivalent to outdoor exhaust."
                ),
                frequency="daily",
            ),
        )

    if assessment.cleaning_frequency in {"less", "monthly"}:
        _add(
            rules,
            RecommendationDraft(
                rule_id="IND-CLEAN-FREQUENCY",
                category="dust",
                title="Increase damp cleaning of high-traffic surfaces",
                description=(
                    "Infrequent cleaning allows dust to accumulate and become "
                    "airborne again."
                ),
                issue="Cleaning was reported as monthly or less frequent.",
                action=(
                    "Damp-wipe high-touch and high-traffic surfaces weekly, and "
                    "vacuum with a suitable filter where available."
                ),
                priority_score=210,
                evidence=EPA_SOURCE_CONTROL,
                expected_benefit="May reduce settled dust and resuspension.",
                limitations=(
                    "Cleaning does not remove a source such as renovation dust or "
                    "outdoor infiltration."
                ),
                frequency="weekly",
            ),
        )

    for sample in sensors:
        recommendation = _sensor_rule(sample)
        if recommendation is not None:
            _add(rules, recommendation)

    has_windows = any(room.windows_count > 0 for room in assessment.rooms)
    has_purifier = any(room.has_purifier for room in assessment.rooms)
    for recommendation in _outdoor_rules(
        outdoor,
        has_windows=has_windows,
        has_purifier=has_purifier,
        sensitive=sensitive,
    ):
        _add(rules, recommendation)

    if not rules:
        _add(
            rules,
            RecommendationDraft(
                rule_id="IND-GENERAL-CHECK",
                category="general",
                title="Keep source control and ventilation in your routine",
                description=(
                    "No specific source or measured issue was selected. A short "
                    "check of cooking exhaust, damp areas and dust is still useful."
                ),
                issue="No specific indoor issue was reported.",
                action=(
                    "Check that cooking exhaust works, bathrooms dry out, and damp "
                    "cleaning happens regularly."
                ),
                priority_score=120,
                evidence=EPA_SOURCE_CONTROL,
                expected_benefit="Maintains a basic indoor-air routine.",
                limitations="General guidance only; no indoor measurement was used.",
                frequency="weekly",
            ),
        )

    ordered = sorted(
        rules.values(),
        key=lambda item: (
            -item.priority_score,
            item.category,
            item.rule_id,
        ),
    )

    high = sum(1 for item in ordered if item.priority == "high")
    medium = sum(1 for item in ordered if item.priority == "medium")
    low = len(ordered) - high - medium
    top_titles = "; ".join(item.title for item in ordered[:3])
    summary = (
        f"Generated {len(ordered)} indoor actions: {high} high, {medium} medium "
        f"and {low} low priority. Priorities reflect selected sources, room "
        f"characteristics and available measurements. Start with: {top_titles}. "
        "This is general household guidance, not a measurement or a diagnosis."
    )
    if sensors and outdoor.available:
        confidence = "high"
    elif sensors or outdoor.available:
        confidence = "medium"
    else:
        confidence = "low"

    limitations = [
        "Outdoor concentrations do not determine indoor concentrations; building "
        "characteristics, sources and filtration all matter.",
        "No action here guarantees pollutant removal or a specific health benefit.",
        "The app does not diagnose mould, chemical contamination or a medical condition.",
    ]
    if not sensors:
        limitations.append(
            "Indoor sensor data is unavailable. No indoor measurement was used."
        )
    elif any(sample.calibration_status != "verified" for sample in sensors):
        limitations.append(
            "At least one indoor sensor is not independently calibrated; readings "
            "are indicators, not certified reference monitoring."
        )
    if not outdoor.available:
        limitations.append(
            "Outdoor air-quality context is unavailable, so ventilation timing is "
            "not personalised to current outdoor conditions."
        )
    elif outdoor.stale:
        limitations.append(
            "The outdoor observation is stale; it is shown with its timestamp and "
            "must not be treated as current."
        )
    if not outdoor.forecast_available:
        limitations.append(
            "A forecast ventilation window could not be calculated from the "
            "available data."
        )

    assumptions = [
        "The assessment describes the rooms and sources as reported by the user.",
        "Room volume is estimated from the reported floor area and ceiling height.",
        "Priority scores are planning aids with documented base weights; they are "
        "not exposure or health-risk scores.",
    ]
    if sensors:
        assumptions.append(
            "The latest valid reading for each pollutant is used; stale readings "
            "are excluded from rule triggers."
        )
    return PlanDraft(
        recommendations=tuple(ordered),
        summary=summary,
        confidence=confidence,
        assumptions=tuple(assumptions),
        limitations=tuple(limitations),
    )
