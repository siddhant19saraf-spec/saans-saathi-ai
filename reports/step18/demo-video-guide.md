# SAANS SAATHI AI — Demo Video Guide

## Purpose
This guide provides a structured script and workflow for recording a demo video that showcases the actual working features of SAANS SAATHI AI for the PromptWars Virtual Challenge 6. No fake metrics, no API keys, no fabricated data.

## Video Requirements (per challenge guidelines)
- **Duration**: 3-5 minutes
- **Format**: MP4 or WebM
- **Content**: Actual running application — no screenshots, no mockups, no artificial benchmarks
- **No API keys** displayed or referenced
- **No fabricated readings** or made-up metrics
- **Show real features** working end-to-end

## Recording Workflow

### Scene 1: Landing Page (0:00-0:20)
- **Action**: Open `http://localhost:3000/`
- **Verification**: Product identity "Every Breath Matters.Every Decision Counts." visible
- **Verification**: All 7 module CTA links visible: Air Intelligence, Family Intelligence, SmartRoutine, IndoorShield, EcoRoute, Impact Intelligence, SAANS AI Copilot
- **Verification**: CPCB 2014 AQI banner with "no fabricated readings · provenance shown with data"
- **Verification**: "INTERFACE PREVIEW · NOT LIVE DATA" clearly stated
- **Screenshot/Frame**: Landing page showing product identity and module links

### Scene 2: Family Intelligence (0:20-0:40)
- **Action**: Click "Family Intelligence" CTA → navigate to `/family`
- **Action**: Health consent checkbox → proceed to household form
- **Action**: Enter test household: name "Test Household", city "New Delhi", timezone "Asia/Kolkata", lat 28.6139, lon 77.2090
- **Action**: Save profile → verify banner "Anonymous session started. Create the household profile below."
- **Verification**: Profile data persists on refresh
- **Screenshot/Frame**: Family page with household form and session gate

### Scene 3: SmartRoutine AI (0:40-1:00)
- **Action**: Navigate to `/smart-routine`
- **Action**: Add activity: title "Morning walk", start "08:00", duration 30 min, venue "outdoor", intensity "moderate"
- **Verification**: Activity added; "Your day" card shows 1 activity, ordered by start time
- **Action**: Add another activity to demonstrate up-to-12 limit
- **Verification**: Timing guidance advisory: "Timing guidance is not connected"
- **Screenshot/Frame**: SmartRoutine planner with activities

### Scene 4: IndoorShield AI (1:00-1:20)
- **Action**: Navigate to `/indoor-shield`
- **Action**: Check 4/8 shelter checklist items (e.g., ventilation, windows closed, no sensors, air exchange)
- **Action**: Save → verify "no indoor sensor data is claimed" banner
- **Verification**: Ventilation guidance displayed: "Ventilate when outdoor PM2.5 is lowest, typically early morning in many Indian cities. This is general guidance, not a reading from a sensor in your home."
- **Screenshot/Frame**: IndoorShield assessment with checklist progress

### Scene 5: EcoRoute AI (1:20-1:40)
- **Action**: Navigate to `/eco-route`
- **Action**: Select transport modes: walking, cycling
- **Action**: Enter distance: 5km
- **Verification**: Comparison renders with emission factor labels (DEFRA 2023, IPCC 2006, CEA v22)
- **Verification**: "No route is drawn or scored on this device. Pollution exposure is only shown when the comparison service returns an exposure index built from real air-quality data; otherwise the column stays empty."
- **Screenshot/Frame**: EcoRoute mode comparison with emission factors

### Scene 6: Impact Intelligence (1:40-2:00)
- **Action**: Navigate to `/impact`
- **Action**: Log an activity: type "walked", quantity 5 km, date today
- **Verification**: Entry appears in "Your log" list (newest first)
- **Verification**: Disclaimer: "Amounts are the quantities you entered, not savings."
- **Verification**: Factor provenance displayed: DEFRA 2023, IPCC 2006, CEA v22
- **Screenshot/Frame**: Impact log with activity entry and factor provenance

### Scene 7: SAANS AI Copilot (2:00-2:20)
- **Action**: Navigate to `/copilot`
- **Verification**: Conversation UI present; "No messages yet" placeholder; question input present
- **Action**: Type a normal question: "When is air quality best for a morning walk?"
- **Caveat**: Since Gemini API key is not configured, the page displays: "When the service is unavailable, no answer is generated here"
- **Alternative**: If Gemini key is obtained, show a grounded response citing FactPack data
- **Screenshot/Frame**: Copilot conversation UI (with or without live AI)

### Scene 8: Air Quality Detail (2:20-2:40)
- **Action**: Navigate to `/air-quality`
- **Verification**: CPCB index displayed with AQI value (or "unavailable" with reason if no data)
- **Verification**: Pollutant concentrations (PM2.5, PM10, NO₂, SO₂, CO, O₃) with provider labels and observation times
- **Verification**: "model-based data" disclaimer where applicable
- **Verification**: Freshness stated (observation time + TTL)
- **Screenshot/Frame**: Air quality detail page

### Scene 9: Persistence Across Refresh (2:40-3:00)
- **Action**: Refresh browser (F5)
- **Verification**: All data persists: bearer token in localStorage; session state in DB; activities in localStorage; profile data
- **Verification**: No data loss; seamless experience
- **Screenshot/Frame**: Post-refresh state confirming persistence

## Technical Prerequisites for Recording

### Backend
```bash
cd backend
export TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/saans_test
export LOG_LEVEL=INFO
uv run uvicorn app.main:app --port 8000 --loop app.core.loop:selector_loop_factory
```

### Frontend
```bash
cd frontend
# Ensure .env.local exists with:
cat frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev  # reaches "Ready in Xms"
```

### Verification Before Recording
- All 11 routes render with 0 console errors and 0 failed HTTP requests
- 14 of 15 user workflows complete successfully
- Browser persistence verified across refresh
- Mobile viewport (Pixel 7, 390×850) responsive behavior confirmed

## Narration Script (Suggested)

> "This is SAANS SAATHI AI — an urban air-quality and sustainable-living intelligence platform. Every breath matters, every decision counts."
>
> "Here I can see the landing page with all seven module entry points: Air Intelligence, Family Intelligence, SmartRoutine, IndoorShield, EcoRoute, Impact, and the SAANS AI Copilot."
>
> "Let me demonstrate the Family Intelligence module — creating an anonymous household profile. Notice there's no account, no email required. The session is authenticated via a bearer token stored locally."
>
> "In the SmartRoutine module, I can add daily activities — up to 12 are supported. The deterministic scheduler orders them by start time and provides timing guidance."
>
> "The IndoorShield module has a shelter checklist — eight items covering ventilation and air-exchange basics. Importantly, no indoor sensor data is claimed. This is general guidance, not sensor readings."
>
> "EcoRoute compares transportation modes for carbon impact. Here I can select walking or cycling — the emission factors are sourced from DEFRA 2023, IPCC 2006, and CEA v22. No route is drawn or scored; exposure is only shown when real air-quality data is available."
>
> "Impact intelligence logs sustainability activities. The amounts entered are the quantities you provided — not computed savings. A baseline assumption is disclosed as such, not as a measured value."
>
> "The SAANS AI Copilot provides grounded conversation. When the AI service is unavailable, the system clearly states that no answer is generated here — it always falls back to deterministic recommendations."
>
> "Throughout the application, CPCB 2014 National AQI is shown with proper provenance. When data is unavailable, the system reports `status: unavailable` with the reason — no fabricated readings are ever displayed."
>
> "Data persists across browser refresh. All state is stored under an anonymous session — no user accounts, no personal information collected."
>
> "The application is structured for WCAG 2.2 AA accessibility — semantic HTML, ARIA labels, focus indicators, color contrast, skip links, and responsive layouts across mobile and desktop viewports."
>
> "SAANS SAATHI AI — converting environmental data into personalized, reliable decisions for everyday breathing."

## Evidence Artifacts for Demo Video
- All 11 routes verified in real Chromium (Playwright E2E: 2/2 smoke tests pass)
- 15 user workflows: 14 pass, 1 conditional (Copilot AI — documented caveat)
- Zero console errors across all routes and workflows
- Zero failed HTTP requests across all routes and workflows
- Persistence verified across browser refresh (workflow W15)
- Mobile responsive: Pixel 7 viewport (390×850) — sidebar collapses, dialogs full-width, forms single-column, touch targets 44×44 dp
- Backend: 264 tests pass serial; frontend: 143 tests pass; all quality checks clean
- Data integrity: All environmental values have provenance; no fabricated readings; CPCB unavailable honestly reported