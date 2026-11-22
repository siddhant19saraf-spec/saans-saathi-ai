# SAANS SAATHI AI — Backend

FastAPI service for SAANS SAATHI AI: air-quality resolution with CPCB AQI,
household profiles, deterministic routine planning, indoor estimates, eco-route
comparison, the sustainability ledger, and a grounded copilot.

See the repository root `README.md` and `docs/BLUEPRINT.md`.

## Quick start

```bash
uv sync
uv run alembic upgrade head        # requires DATABASE_URL
uv run uvicorn app.main:app --reload --port 8000
```

Health check: <http://localhost:8000/readyz>

On Windows, uvicorn chooses the Proactor loop when it is not spawning a reload
subprocess, and psycopg's async driver refuses that loop. Use the selector
factory when running without `--reload`:

```bash
uv run uvicorn app.main:app --port 8000 --loop app.core.loop:selector_loop_factory
```

## Tests

Database-backed tests run against a real PostgreSQL instance and are skipped
when `TEST_DATABASE_URL` is unset:

```bash
TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:5432/saans_saathi_test \
  uv run pytest
```

## Quality gates

```bash
uv run ruff check .
uv run black --check .
uv run mypy app
uv run bandit -c pyproject.toml -r app
uv run pytest
```
