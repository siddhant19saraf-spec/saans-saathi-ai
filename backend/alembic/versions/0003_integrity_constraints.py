"""integrity constraints and retention indexes

Adds database-level CHECK constraints for coordinates, non-negative
measurements, timestamp chronology and non-empty text, plus indexes used by
retention and foreign-key joins. The existing migration history is untouched.

Revision ID: 0003_integrity_constraints
Revises: 0002_initial_schema
Create Date: 2026-11-19 14:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003_integrity_constraints"
down_revision: str | None = "0002_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_CHECKS: tuple[tuple[str, str, str], ...] = (
    # profiles
    (
        "ck_profiles_expiry_after_created",
        "profiles",
        "expires_at > created_at",
    ),
    (
        "ck_profiles_deleted_after_created",
        "profiles",
        "deleted_at IS NULL OR deleted_at >= created_at",
    ),
    (
        "ck_profiles_consent_version_present",
        "profiles",
        "btrim(consent_version) <> ''",
    ),
    # ai_conversations
    (
        "ck_ai_conversations_expiry_after_created",
        "ai_conversations",
        "expires_at > created_at",
    ),
    (
        "ck_ai_conversations_lat_key_range",
        "ai_conversations",
        "context_lat_key IS NULL OR context_lat_key BETWEEN -90 AND 90",
    ),
    (
        "ck_ai_conversations_lon_key_range",
        "ai_conversations",
        "context_lon_key IS NULL OR context_lon_key BETWEEN -180 AND 180",
    ),
    # ai_messages
    (
        "ck_ai_messages_content_present",
        "ai_messages",
        "btrim(content) <> ''",
    ),
    (
        "ck_ai_messages_input_tokens_non_negative",
        "ai_messages",
        "input_tokens IS NULL OR input_tokens >= 0",
    ),
    (
        "ck_ai_messages_output_tokens_non_negative",
        "ai_messages",
        "output_tokens IS NULL OR output_tokens >= 0",
    ),
    (
        "ck_ai_messages_latency_non_negative",
        "ai_messages",
        "latency_ms IS NULL OR latency_ms >= 0",
    ),
    (
        "ck_ai_messages_fact_pack_hash_length",
        "ai_messages",
        "fact_pack_hash IS NULL OR char_length(fact_pack_hash) = 64",
    ),
    # air_quality_snapshots
    (
        "ck_air_quality_snapshots_lat_key_range",
        "air_quality_snapshots",
        "lat_key BETWEEN -90 AND 90",
    ),
    (
        "ck_air_quality_snapshots_lon_key_range",
        "air_quality_snapshots",
        "lon_key BETWEEN -180 AND 180",
    ),
    (
        "ck_air_quality_snapshots_expiry_after_fetch",
        "air_quality_snapshots",
        "expires_at > fetched_at",
    ),
    (
        "ck_air_quality_snapshots_pollutants_non_negative",
        "air_quality_snapshots",
        "(pm2_5 IS NULL OR pm2_5 >= 0)"
        " AND (pm10 IS NULL OR pm10 >= 0)"
        " AND (co_ug_m3 IS NULL OR co_ug_m3 >= 0)"
        " AND (no2_ug_m3 IS NULL OR no2_ug_m3 >= 0)"
        " AND (so2_ug_m3 IS NULL OR so2_ug_m3 >= 0)"
        " AND (o3_ug_m3 IS NULL OR o3_ug_m3 >= 0)"
        " AND (dust_ug_m3 IS NULL OR dust_ug_m3 >= 0)",
    ),
    (
        "ck_air_quality_snapshots_us_aqi_non_negative",
        "air_quality_snapshots",
        "us_aqi IS NULL OR us_aqi >= 0",
    ),
    (
        "ck_air_quality_snapshots_eu_aqi_non_negative",
        "air_quality_snapshots",
        "eu_aqi IS NULL OR eu_aqi >= 0",
    ),
    (
        "ck_air_quality_snapshots_station_distance_non_negative",
        "air_quality_snapshots",
        "station_distance_km IS NULL OR station_distance_km >= 0",
    ),
    # air_quality_forecasts
    (
        "ck_air_quality_forecasts_lat_key_range",
        "air_quality_forecasts",
        "lat_key BETWEEN -90 AND 90",
    ),
    (
        "ck_air_quality_forecasts_lon_key_range",
        "air_quality_forecasts",
        "lon_key BETWEEN -180 AND 180",
    ),
    (
        "ck_air_quality_forecasts_expiry_after_issue",
        "air_quality_forecasts",
        "expires_at > issued_at",
    ),
    # air_quality_fetch_log
    (
        "ck_air_quality_fetch_log_http_status_range",
        "air_quality_fetch_log",
        "http_status IS NULL OR http_status BETWEEN 100 AND 599",
    ),
    (
        "ck_air_quality_fetch_log_latency_non_negative",
        "air_quality_fetch_log",
        "latency_ms IS NULL OR latency_ms >= 0",
    ),
    (
        "ck_air_quality_fetch_log_lat_key_range",
        "air_quality_fetch_log",
        "lat_key IS NULL OR lat_key BETWEEN -90 AND 90",
    ),
    (
        "ck_air_quality_fetch_log_lon_key_range",
        "air_quality_fetch_log",
        "lon_key IS NULL OR lon_key BETWEEN -180 AND 180",
    ),
    # households
    (
        "ck_households_timezone_present",
        "households",
        "btrim(timezone) <> ''",
    ),
    # household_preferences
    (
        "ck_household_preferences_locale_present",
        "household_preferences",
        "btrim(locale) <> ''",
    ),
    # saved_locations
    (
        "ck_saved_locations_label_present",
        "saved_locations",
        "btrim(label) <> ''",
    ),
    # routines
    (
        "ck_routines_inputs_hash_length",
        "routines",
        "char_length(inputs_hash) = 64",
    ),
    (
        "ck_routines_timezone_present",
        "routines",
        "btrim(timezone) <> ''",
    ),
    (
        "ck_routines_engine_version_present",
        "routines",
        "btrim(engine_version) <> ''",
    ),
    (
        "ck_routines_expiry_after_generated",
        "routines",
        "expires_at > generated_at",
    ),
    # recommendations
    (
        "ck_recommendations_title_present",
        "recommendations",
        "btrim(title) <> ''",
    ),
    (
        "ck_recommendations_body_present",
        "recommendations",
        "btrim(body) <> ''",
    ),
    (
        "ck_recommendations_dismissed_after_created",
        "recommendations",
        "dismissed_at IS NULL OR dismissed_at >= created_at",
    ),
    # sustainability_activities
    (
        "ck_sustainability_activities_co2e_non_negative",
        "sustainability_activities",
        "co2e_kg >= 0",
    ),
    (
        "ck_sustainability_activities_factor_value_non_negative",
        "sustainability_activities",
        "factor_value >= 0",
    ),
    (
        "ck_sustainability_activities_unit_allowed",
        "sustainability_activities",
        "unit IN ('km','days','trees')",
    ),
    (
        "ck_sustainability_activities_factor_key_present",
        "sustainability_activities",
        "btrim(factor_key) <> ''",
    ),
    (
        "ck_sustainability_activities_factor_unit_present",
        "sustainability_activities",
        "btrim(factor_unit) <> ''",
    ),
    (
        "ck_sustainability_activities_factor_version_present",
        "sustainability_activities",
        "btrim(factor_version) <> ''",
    ),
    (
        "ck_sustainability_activities_factor_source_present",
        "sustainability_activities",
        "btrim(factor_source_url) <> ''",
    ),
    # usage_daily
    (
        "ck_usage_daily_requests_non_negative",
        "usage_daily",
        "requests >= 0",
    ),
    (
        "ck_usage_daily_input_tokens_non_negative",
        "usage_daily",
        "input_tokens >= 0",
    ),
    (
        "ck_usage_daily_output_tokens_non_negative",
        "usage_daily",
        "output_tokens >= 0",
    ),
)

_INDEXES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("ix_profiles_expires", "profiles", ("expires_at",)),
    ("ix_ai_conversations_expiry", "ai_conversations", ("expires_at",)),
    ("ix_snap_expiry", "air_quality_snapshots", ("expires_at",)),
    ("ix_forecast_expiry", "air_quality_forecasts", ("expires_at",)),
    ("ix_recs_routine", "recommendations", ("routine_id",)),
)


def upgrade() -> None:
    for name, table, condition in _CHECKS:
        op.create_check_constraint(op.f(name), table, condition)

    # The API never accepted 'none'; tighten the old constraint to the
    # documented health-flag vocabulary.
    op.drop_constraint(
        op.f("ck_household_members_health_flags_allowed"),
        "household_members",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_household_members_health_flags_allowed"),
        "household_members",
        "health_flags <@ ARRAY['asthma','allergy','copd','heart','pregnant']",
    )

    for name, table, columns in _INDEXES:
        op.create_index(name, table, list(columns), unique=False)


def downgrade() -> None:
    for name, table, _columns in reversed(_INDEXES):
        op.drop_index(name, table_name=table)

    op.drop_constraint(
        op.f("ck_household_members_health_flags_allowed"),
        "household_members",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_household_members_health_flags_allowed"),
        "household_members",
        "health_flags <@ ARRAY"
        "['asthma','allergy','copd','heart','pregnant','none']",
    )

    for name, table, _condition in reversed(_CHECKS):
        op.drop_constraint(op.f(name), table, type_="check")
