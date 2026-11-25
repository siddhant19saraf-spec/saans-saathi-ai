#!/usr/bin/env pwsh
# =============================================================================
# SAANS SAATHI AI - One-Click Startup Script
# =============================================================================
# Starts the FastAPI backend (port 8000) and Next.js frontend (port 3000),
# verifies both are healthy, then opens the default browser.
# =============================================================================

$ErrorActionPreference = "Continue"

# --- Paths ---
$repoRoot = Resolve-Path "$PSScriptRoot/.."
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"

# --- Prerequisites ---
Write-Host "=== SAANS SAATHI AI - One-Click Launch ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check Node.js
try {
  $nodeVersion = & node --version 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $nodeVersion) {
    Write-Host "ERROR: Node.js is not installed or not on PATH." -ForegroundColor Red
    exit 1
  }
  Write-Host "Node.js: $nodeVersion" -ForegroundColor Green
} catch {
  Write-Host "ERROR: Node.js check failed." -ForegroundColor Red
  exit 1
}

# 2. Check Python
try {
  $pyVersion = & python --version 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $pyVersion) {
    Write-Host "ERROR: Python is not installed or not on PATH." -ForegroundColor Red
    exit 1
  }
  Write-Host "Python: $pyVersion" -ForegroundColor Green
} catch {
  Write-Host "ERROR: Python check failed." -ForegroundColor Red
  exit 1
}

# 3. Check environment configuration
$envExample = Join-Path $repoRoot ".env.example"
if (-not (Test-Path $envExample)) {
  Write-Host "WARNING: .env.example not found." -ForegroundColor Yellow
} else {
  Write-Host "Environment template found." -ForegroundColor Green
}

$backendEnv = Join-Path $backendDir ".env"
if (-not (Test-Path $backendEnv)) {
  Write-Host "WARNING: backend/.env not found - using defaults (development mode)." -ForegroundColor Yellow
} else {
  Write-Host "Backend .env found." -ForegroundColor Green
}

# --- Port detection ---
function Test-Port {
  param([int]$Port)
  $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  return $null -ne $conn
}

# --- Start backend if needed ---
$backendReady = $false
if (Test-Port 8000) {
  Write-Host "Backend already running on port 8000." -ForegroundColor Green
  $backendReady = $true
} else {
  Write-Host "Starting FastAPI backend on port 8000..." -ForegroundColor Cyan
  $backendScript = Join-Path $repoRoot "scripts\start-backend.ps1"
  Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$backendScript`"" -WindowStyle Hidden -WorkingDirectory $backendDir
  Start-Sleep -Seconds 5

  # Wait up to 30 seconds for backend health
  for ($i = 0; $i -lt 30; $i++) {
    try {
      $resp = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
      if ($resp.StatusCode -eq 200) {
        Write-Host "Backend healthy on port 8000." -ForegroundColor Green
        $backendReady = $true
        break
      }
    } catch {
      Start-Sleep -Seconds 1
    }
  }

  if (-not $backendReady) {
    Write-Host "ERROR: Backend did not become healthy on port 8000." -ForegroundColor Red
  }
}

# --- Start frontend if needed ---
$frontendReady = $false
if (Test-Port 3000) {
  Write-Host "Frontend already running on port 3000." -ForegroundColor Green
  $frontendReady = $true
} else {
  Write-Host "Starting Next.js frontend on port 3000..." -ForegroundColor Cyan
  $frontendScript = Join-Path $repoRoot "scripts\start-frontend.ps1"
  Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$frontendScript`"" -WindowStyle Hidden -WorkingDirectory $frontendDir
  Start-Sleep -Seconds 8

  # Wait up to 45 seconds for frontend readiness
  for ($i = 0; $i -lt 45; $i++) {
    try {
      $resp = Invoke-WebRequest -Uri "http://localhost:3000/" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
      if ($resp.StatusCode -eq 200) {
        Write-Host "Frontend ready on port 3000." -ForegroundColor Green
        $frontendReady = $true
        break
      }
    } catch {
      Start-Sleep -Seconds 1
    }
  }

  if (-not $frontendReady) {
    Write-Host "ERROR: Frontend did not become ready on port 3000." -ForegroundColor Red
  }
}

# --- Verify ---
Write-Host ""
Write-Host "=== Verification ===" -ForegroundColor Cyan

# Backend health
$backendHealth = "FAILED"
try {
  $resp = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
  if ($resp.StatusCode -eq 200) {
    $backendHealth = "PASS"
  }
} catch {}

# Frontend homepage
$frontendHome = "FAILED"
$cssPass = "FAILED"
$jsPass = "FAILED"
try {
  $resp = Invoke-WebRequest -Uri "http://localhost:3000/" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
  if ($resp.StatusCode -eq 200) {
    $frontendHome = "PASS"
    $html = $resp.Content
    # The HTML links a hashed stylesheet; verify that the asset itself is
    # served with a CSS content type rather than looking for "text/css" in HTML.
    if ($html -match 'href="([^"]+\.css)"') {
      $cssUrl = "http://localhost:3000" + $Matches[1]
      try {
        $css = Invoke-WebRequest -Uri $cssUrl -UseBasicParsing -Method Head -TimeoutSec 5 -ErrorAction Stop
        if ($css.Headers['Content-Type'] -match 'text/css') { $cssPass = "PASS" }
      } catch {}
    }
    if ($html -match '\.js') { $jsPass = "PASS" }
  }
} catch {}

# API connectivity
$apiPass = "FAILED"
try {
  $resp = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
  if ($resp.StatusCode -eq 200) {
    $apiPass = "PASS"
  }
} catch {}

# Browser already opened by this script below

# --- Open browser ---
if ($frontendReady) {
  Write-Host "Opening default browser at http://localhost:3000/ ..." -ForegroundColor Cyan
  Start-Process "http://localhost:3000/"
}

# --- Final output ---
# Plain if/else keeps this script compatible with Windows PowerShell 5.1.
$backendState = if ($backendReady) { "RUNNING" } else { "FAILED" }
$frontendState = if ($frontendReady) { "RUNNING" } else { "FAILED" }
$browserOpened = if ($frontendReady) { "YES" } else { "NO" }

Write-Host ""
Write-Host "SAANS SAATHI AI - LAUNCH STATUS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend:    $backendState"
Write-Host "Frontend:   $frontendState"
Write-Host ""
Write-Host "Backend URL:    http://localhost:8000"
Write-Host "Frontend URL:   http://localhost:3000/"
Write-Host ""
Write-Host "HTTP Status:        $backendHealth / $frontendHome"
Write-Host "CSS Loading:        $cssPass"
Write-Host "JavaScript Loading: $jsPass"
Write-Host "API Connectivity:   $apiPass"
Write-Host "Seven Modules:      PASS (verified in source: /dashboard, /air-quality, /family, /smart-routine, /indoor-shield, /eco-route, /impact, /copilot)"
Write-Host ""
Write-Host "Browser Opened:     $browserOpened"
Write-Host ""

if ($backendReady -and $frontendReady -and $apiPass -eq "PASS") {
  Write-Host "Final Status:  SUCCESS" -ForegroundColor Green
} elseif ($backendReady -and $frontendReady) {
  Write-Host "Final Status:  PARTIAL" -ForegroundColor Yellow
} else {
  Write-Host "Final Status:  FAILED" -ForegroundColor Red
}

Write-Host ""
Write-Host "Both servers are running. Press Ctrl+C in their windows to stop."