#!/usr/bin/env pwsh
# Starts the SAANS SAATHI AI Next.js frontend on port 3000.
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $repoRoot "frontend")

& npx next start --port 3000
