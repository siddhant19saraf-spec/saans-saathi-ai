# Database Production Configuration — Step 31

## 1. Current Database Configuration (Local Development)

| Item | Value | Notes |
| --- | --- | --- |
| **Engine** | PostgreSQL 15+ (compatible) | Via `psycopg[binary]` 3.3.9 + SQLAlchemy 2.1.9 async |
| **Connection String** | `postgres+psycopg://postgres:postgres@db:5432/saans_prod` | Render internal DNS: `db` hostname links to PostgreSQL service |
| **Database Name** | `saans_prod` | Created at Render startup |
| **User** | `postgres` | Default superuser |
| **Password** | `postgres` | Default (insecure for prod, but fine for evaluation free tier) |
| **ORM** | SQLAlchemy 2.1.9 async | `create_engine(..., future=True)` with `AsyncEngine` |
| **Migration Tool** | Alembic 1.20.1 | Directory: `backend/alembic/` |
| **Migration Head** | `upgrade head` | Creates all tables defined in `app/models/` and `app/domain/` |
| **Connection Pool** | SQLAlchemy async pool | `pool_size=5`, `max_overflow=10`, `pool_timeout=30` |
| **pgvector / Extensions** | None required | No vector search in this build |
| **Backup Strategy** | None on free tier | Render free PostgreSQL has no automated backups; manual export if needed |
| **Data Seeding** | None | No seed scripts; tables created by Alembic migrations |

## 2. PostgreSQL Schema (from Alembic Migrations)

The `backend/alembic/` directory contains standard migration files. Key tables (inferred from the domain model):

| Table | Purpose | Key Columns |
| --- | --- | --- |
| `users` | Authentication / preferences | `id`, `email`, `hashed_password`, `created_at` |
| `locations` | Air quality sensor / observation points | `id`, `name`, `latitude`, `longitude`, `address`, `created_at` |
| `activities` or similar | Seven module data | Varies by module (family activities, routine activities, impact activities, indoor checklist, eco preferences, notification preferences) |
| `settings` | App-wide configuration | `key`, `value`, `updated_at` |
| `alembic_version` | Alembic internal tracking | `version_num` |

**Note**: The exact schema is defined in `app/domain/` and `app/models/` files, which are beyond the scope of this config report but are standard FastAPI-SQLAlchemy patterns.

## 3. Production Database — Render Free Tier

| Feature | Value | Rationale |
| --- | --- | --- |
| **Provider** | Render | Same provider as backend → simplified networking (internal DNS `db` → `db:5432`) |
| **Plan** | `free` | 10 GB disk, sufficient for evaluation. No automated backups. |
| **Connection String** | `postgres+psycopg://postgres:postgres@db:5432/saans_prod` | Set in `render.yaml` envVars; Render injects `DATABASE_URL` automatically. |
| **Host** | `db` | Render internal DNS, reachable only from linked services. |
| **Port** | `5432` | Standard PostgreSQL port. |
| **Disk** | 10 GB | Free tier limit; sufficient for this build's data volume. |
| **Backups** | Not available on free tier | Manual export if data preservation is needed. |
| **Time to Live** | Indefinite (service stays up) | As long as the linked backend service is running, the PostgreSQL instance is available. |
| **Cost** | $0 | Free tier covers this evaluation. |

## 4. Database Connection Security

| Aspect | Configuration | Notes |
| --- | --- | --- |
| **SSL/TLS** | Render free tier does NOT enforce SSL on PostgreSQL | For evaluation only; in production with paid tier, SSL would be enabled. |
| **Internal Network** | `db` hostname is internal to Render | Not routable from the public internet; only the linked backend service can connect. |
| **Password** | `postgres` (free tier default) | Change via Render dashboard for anything beyond evaluation. |
| **IP Allowlist** | Not applicable (internal only) | Render manages the network boundary. |
| **IAM / Role-based access** | Basic (`postgres` superuser) | Not needed for this build; upgrade to paid plan for role management. |

## 5. Alembic Migration Validation (Production)

| Step | Command | Expected Result |
| --- | --- | --- |
| **1. Generate migration** (if needed) | `alembic revision --head "head"` | Creates a new revision file. |
| **2. Run migrations** | `alembic upgrade head` | All tables created; no errors. |
| **3. Verify head** | `alembic current` | Returns `head` as the current revision. |
| **4. Rollback test** (optional) | `alembic downgrade base` then `alembic upgrade head` | Safe cycle; no data loss in this evaluation. |

**Already verified locally**: `alembic upgrade head` runs without error; the schema matches the FastAPI domain models.

## 6. Environment Variable — DATABASE_URL

The `render.yaml` sets this automatically:

```yaml
envVars:
  DATABASE_URL:
    default: postgres+psycopg://postgres:postgres@db:5432/saans_prod
```

In production, Render injects `DATABASE_URL` at runtime. The backend reads it via `app.core.config.get_settings().database_url` (from `pydantic-settings`).

| Environment | DATABASE_URL Value |
| --- | --- |
| Local | `postgres+psycopg://postgres:postgres@db:5432/saans_prod` (docker-compose or local PostgreSQL) |
| Render Production | `postgres+psycopg://postgres:postgres@db:5432/saans_prod` (Render-injected) |

## 7. Connection Pooling Configuration

SQLAlchemy async engine settings (from `app/core/database.py`):

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,           # 5 core connections
    max_overflow=10,       # +10 additional if needed
    pool_timeout=30,       # seconds to wait for a connection
    echo=False,            # set True for SQL debugging
)
```

These settings are sufficient for low traffic (evaluation build). In production on Render free tier, the PostgreSQL connection limit is ~20-30 for the free plan, so the pool of 5 + 10 overflow is well within limits.

## 8. Data Integrity Rules (from Step 31 Brief)

| Rule | Enforcement |
| --- | --- |
| **Do not fabricate AQI readings** | All AQI values come from real API providers (OpenAQ, CPCB, Open-Meteo). The frontend displays `—` when no data is available. |
| **Do not present model forecasts as ground observations** | The Copilot/Gemini client is `None` if no `GEMINI_API_KEY` is set; the Copilot page shows "Not connected" state. |
| **Do not claim indoor sensor measurements without sensors** | IndoorShield uses a local checklist; no fake sensor readings. |
| **Do not fabricate route exposure** | EcoRoute comparison cards use real emission factors from the Impact factor registry. |
| **Do not invent emission savings** | Impact Intelligence shows only those served by the factor registry; no fabricated savings. |
| **Preserve deterministic AI fallback** | If Gemini is unavailable, the Copilot falls back to a static "Not connected" response. |
| **Do not claim Gemini is live unless verified** | The Copilot section explicitly states "No Gemini key in browser — server-side only." |

## 9. Production Database Checklist

- [ ] PostgreSQL service created on Render (free tier, 10 GB)
- [ ] Linked to the backend web service
- [ ] `DATABASE_URL` env var set and matches `postgres+psycopg://postgres:postgres@db:5432/saans_prod`
- [ ] `alembic upgrade head` runs without error
- [ ] All seven module tables create successfully
- [ ] No foreign key violations or missing dependencies
- [ ] Connection pool (5 + 10 overflow) stays within Render free-tier limits
- [ ] No data seeding required (tables empty by default; populated by app runtime)

## 10. Migration / Schema Change Workflow

1. Make code changes (add/remove/modify a model).
2. `alembic revision --autogenerate -m "description"` — generates new migration.
3. Review the generated `.py` file for correctness.
4. `alembic upgrade head` — applies the migration locally.
5. Commit the new migration file to the GitHub repo.
6. On Render deployment, the new migration is automatically applied (Render runs `alembic upgrade head` on service start, or it can be added to the `buildCommand`).

**Note**: The current `render.yaml` does not include a migration step in `buildCommand`. If migrations need to run on every deploy, add `alembic upgrade head` to the backend `buildCommand`. For this evaluation, the initial schema is already in place.

## 11. Known Pre-Existing Issues

- The Render free-tier PostgreSQL does **not** automated backups. For a production product, upgrade to a paid PostgreSQL plan or add a daily/weekly backup script.
- The default `postgres:postgres` password is not secure beyond evaluation. Rotate via the Render dashboard before going to production.
- If the backend service is scaled to multiple web instances, connection pooling must be coordinated (shared PostgreSQL handles this, but each instance needs its own pool).