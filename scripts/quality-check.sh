#!/usr/bin/env bash
# Run every quality gate locally, in the same order as CI.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "==> Backend: dependency sync"
(cd backend && uv sync)

echo "==> Backend: Ruff"
(cd backend && uv run ruff check .)

echo "==> Backend: Black"
(cd backend && uv run black --check .)

echo "==> Backend: MyPy"
(cd backend && uv run mypy app)

echo "==> Backend: Bandit"
(cd backend && uv run bandit -c pyproject.toml -r app)

echo "==> Backend: pip-audit"
(cd backend && uv run pip-audit)

echo "==> Backend: Pytest"
(cd backend && uv run pytest --cov --cov-report=term-missing)

echo "==> Frontend: dependencies"
if [ ! -d frontend/node_modules ]; then
  (cd frontend && npm ci)
fi

echo "==> Frontend: ESLint"
(cd frontend && npm run lint)

echo "==> Frontend: Prettier"
(cd frontend && npm run format:check)

echo "==> Frontend: TypeScript"
(cd frontend && npm run typecheck)

echo "==> Frontend: Vitest"
(cd frontend && npm run test)

echo "==> Frontend: production build"
(cd frontend && npm run build)

echo "==> Repository size"
bash scripts/check-repo-size.sh 10

echo "All quality gates passed."
