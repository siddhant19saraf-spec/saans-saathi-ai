#!/usr/bin/env pwsh
# Starts the SAANS SAATHI AI FastAPI backend on port 8000.
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
Set-Location $backendDir

# Load backend/.env when present. Values are not printed.
$envFile = Join-Path $backendDir ".env"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
      $name = $Matches[1]
      $value = $Matches[2].Trim().Trim('"').Trim("'")
      [Environment]::SetEnvironmentVariable($name, $value, [EnvironmentVariableTarget]::Process)
    }
  }
}

# Development defaults when .env does not provide them.
if (-not $env:DATABASE_URL) {
  $env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/saans_dev"
}
if (-not $env:ALLOWED_ORIGINS) {
  $env:ALLOWED_ORIGINS = "http://localhost:3000"
}

$python = Join-Path $backendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  $python = "python"
}

& $python -m uvicorn app.main:app --port 8000 --loop app.core.loop:selector_loop_factory
