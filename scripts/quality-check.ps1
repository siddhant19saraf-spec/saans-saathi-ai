# Run every quality gate locally, in the same order as CI (Windows PowerShell).
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    function Invoke-Step {
        param([string]$Label, [scriptblock]$Action)
        Write-Host "==> $Label"
        & $Action
        if ($LASTEXITCODE -ne 0) {
            throw "$Label failed with exit code $LASTEXITCODE"
        }
    }

    Push-Location backend
    try {
        Invoke-Step "Backend: dependency sync" { uv sync }
    }
    finally {
        Pop-Location
    }

    Push-Location backend
    try {
        Invoke-Step "Backend: Ruff" { uv run ruff check . }
        Invoke-Step "Backend: Black" { uv run black --check . }
        Invoke-Step "Backend: MyPy" { uv run mypy app }
        Invoke-Step "Backend: Bandit" { uv run bandit -c pyproject.toml -r app }
        Invoke-Step "Backend: pip-audit" { uv run pip-audit }
        Invoke-Step "Backend: Pytest" { uv run pytest --cov --cov-report=term-missing }
    }
    finally {
        Pop-Location
    }

    if (-not (Test-Path "frontend/node_modules")) {
        Push-Location frontend
        try {
            Invoke-Step "Frontend: dependencies" { npm ci }
        }
        finally {
            Pop-Location
        }
    }

    Push-Location frontend
    try {
        Invoke-Step "Frontend: ESLint" { npm run lint }
        Invoke-Step "Frontend: Prettier" { npm run format:check }
        Invoke-Step "Frontend: TypeScript" { npm run typecheck }
        Invoke-Step "Frontend: Vitest" { npm run test }
        Invoke-Step "Frontend: production build" { npm run build }
    }
    finally {
        Pop-Location
    }

    Invoke-Step "Repository size" { bash scripts/check-repo-size.sh 10 }

    Write-Host "All quality gates passed."
}
finally {
    Pop-Location
}
