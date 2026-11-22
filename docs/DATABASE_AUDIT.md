# SAANS SAATHI AI — Database Audit

**Audit date:** 2026-11-21  
**Database:** PostgreSQL 16.15 (local)  
**Connection:** `postgresql+psycopg://postgres:postgres@localhost:5432/saans_test` (isolated test DB only)  
**ORM:** SQLAlchemy async with Alembic migrations

---

## Schema Overview

**28 tables** exposed via SQLAlchemy `Base.metadata`:

| Table group | Tables |
|-------------|--------|
| Core | `profiles`, `sessions`, `households`, `household_members`, `household_preferences` |
| Saved locations | `saved_locations` |
| SmartRoutine | `routine_activities`, `routines`, `routine_items` |
| Impact ledger | `sustainability_activities`, `sustainability_goals` |
| Indoor Shield | `indoor_assessments`, `indoor_recommendations`, `indoor_actions`, `indoor_action_events`, `indoor_sensors`, `indoor_sensor_readings` |
| EcoRoute | `saved_journeys`, `emission_calculations` |
| Conversations | `conversations`, `conversation_messages` |
| Air quality | `air_cache_entries` |
| Validation | `ai_validations` |

## Migrations

**9 Alembic revisions** (`backend/alembic/versions/`):

| Revision | Description |
|----------|-------------|
| `0001_baseline` | Initial schema |
| `0002` – `0007` | Incremental schema additions |
| `0008` | Added check constraints (shipped; not modified) |
| `0009_constraint_names` | **Fixes 8 constraint-name drifts** from `0008` |

### Constraint Drift (Resolved)

Migration `0008` created 8 check constraints with names that did not match SQLAlchemy ORM metadata. This caused schema validation failures when tests compared ORM metadata against the actual database.

**Fix:** Created forward migration `0009_constraint_names.py` that renames all 8 constraints to match ORM metadata. Did not edit already-shipped `0008` (preserves git history and migration integrity).

**Verification:** `tests/test_migrations.py` (2 tests) passes; migration test expects revision `0009_constraint_names`.

---

## Test Database Strategy

- **Isolated DB:** `saans_test` database used for all DB-backed tests
- **Schema setup:** `Base.metadata.drop_all()` + `create_all()` per session; tables truncated around each test
- **Skip behavior:** DB-backed tests skipped when `TEST_DATABASE_URL` is not set (82 previously skipped tests now run locally)
- **Windows fix:** `asyncio.WindowsSelectorEventLoopPolicy` set in `conftest.py` for psycopg async on Windows
- **No production DB operations:** Tests never touch production databases; no destructive operations

---

## Repository Layer Audit

| Repository | Methods | Coverage notes |
|------------|---------|----------------|
| `households` | `get_for_profile`, `create`, `update`, `list_members`, `add_member`, `get_member`, `update_member`, `delete_member`, `get_preferences`, `ensure_preferences`, `update_preferences`, `list_locations`, `add_location`, `get_location`, `delete_location`, `find_location_by_label` | Well tested via household tests |
| `routines` | `list_activities`, `get_activity`, `count_activities`, `add_activity`, `delete_activity`, `latest_active_for_date`, `latest_version_for_date`, `find_active_by_inputs`, `get`, `supersede_active`, `add`, `replace_plan`, `history`, `add_item`, `get_item_by_activity` | Well tested via new `test_routine_lifecycle.py` |
| `impact` | `add_activity`, `list_activities`, `summary` | Well tested via `test_impact.py` + `test_impact_ledger.py` |
| `ecoroute` | `create_goal`, `list_goals`, `get_goal`, `update_goal`, `delete_goal`, plus journey/calculation methods | Goals tested via `test_impact_ledger.py` |
| `indoor` | Assessment, sensor, reading methods | Partial coverage |
| `indoor_shield` | Assessment, recommendation, action methods | Partial coverage |
| `air` | Cache entry methods | Partial coverage |
| `conversations` | Conversation/message methods | Partial coverage |
| `profiles` | Profile methods | Partial coverage |
| `recommendations` | Recommendation methods | Partial coverage |

---

## Data Integrity Findings

1. **Check constraints:** 8 constraints renamed in `0009` to match ORM metadata. ✓ Resolved.
2. **Unique constraints:** Location labels unique per household; enforced at DB + application level. ✓
3. **Foreign keys:** All tables reference `profiles.id` or `households.id` with proper FK constraints. ✓
4. **Soft deletes:** Routine activities use `active` flag; indoor sensors use deactivation. ✓
5. **Cascading deletes:** Family profile deletion cascades to recommendations, goals, journeys. ✓
6. **No hardcoded environmental data:** Tests use deterministic fixtures, not real sensor/location data. ✓

---

## Gaps / Limitations

| Area | Detail |
|------|--------|
| Indoor Shield repository | Partial test coverage; `indoor_shield_service.py` at 49% line coverage |
| EcoRoute repository | Partial test coverage; `ecoroute_repo` at 64% line coverage |
| Air quality cache | Partial test coverage |
| Production DB | Not accessible; local test DB only; no production connection string in repo |
| Migration testing | `0009` verified locally; production migration path not tested without deploy access |
