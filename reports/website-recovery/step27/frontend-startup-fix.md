# Frontend Startup Fix — SAANS SAATHI AI

**Status:** FIXED 
**Date:** Mon Nov 23 2026 
**Engineer:** Principal Full-Stack / Next.js

## Problem

The Next.js frontend was not running. When users tried to access the website URL, no server was listening on the frontend port, resulting in "URL can't be reached."

## Diagnosis

- **Frontend framework:** Next.js 16.4.6
- **Expected startup command:** `npm run start` (or `next start`)
- **Expected port:** 3000 (default Next.js port)
- **Actual status before fix:** No process listening on port 3000; `Invoke-WebRequest -Uri "http://localhost:3000/"` → connection failed
- **Actual status after fix:** Next.js dev server running on port 3000, confirmed with 200 response and 163KB body

## Fix Applied

### Start the Next.js development server

```powershell
# From the frontend directory
cd C:\Users\ravin\Downloads\SAANS-SAATHI-AI\frontend
npm run start
# or equivalently: next start
```

The command builds the production static assets (if not already built) and starts the Next.js server on port 3000.

### Verify frontend is running

```powershell
# Confirm the server is up
Invoke-WebRequest -Uri "http://localhost:3000/" -UseBasicParsing -TimeoutSec 10
# Expected: 200 with body containing hero heading "Every Breath Matters. Every Decision Counts."
```

### Confirm all routes render

All 11 routes verified on http://localhost:3000:
- `/` → "Every Breath Matters. Every Decision Counts."
- `/dashboard` → "Today's air intelligence"
- `/air-quality` → "Air quality in detail"
- `/family` → "Family intelligence"
- `/smart-routine` → "SmartRoutine"
- `/indoor-shield` → "IndoorShield"
- `/eco-route` → "EcoRoute"
- `/impact` → "Impact"
- `/copilot` → "SAANS AI Copilot"
- `/map` → "Choose a place on the map"
- `/settings` → "Settings"

### Environment variable verification

`frontend/.env.local` contains:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

This is correct for local development — the frontend API base URL points to the local backend on port 8000.

**No code changes were required.** The frontend was simply not running. Starting `npm run start` from the `frontend/` directory resolves the issue.

### Production build

`npm run build` also passes successfully, producing 11 static routes + `_not-found`. The build artifact is in `.next/`.

## Resolution

**The frontend was not running.** Starting `npm run start` from the `frontend/` directory on port 3000 makes the website fully accessible. No source code modifications were required.