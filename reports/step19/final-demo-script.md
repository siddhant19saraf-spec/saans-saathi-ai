# SAANS SAATHI AI — Final Demo Script

## Video Specifications
- **Duration**: 3-5 minutes
- **Format**: MP4 (recommended) or WebM
- **Recording**: Actual browser screen recording (no mockups, no screenshots of mockups)
- **Narrations**: Clear, concise; no background music required
- **Test inputs**: Realistic but non-sensitive (no real household data, no real coordinates)
- **No API keys displayed** at any point
- **No fabricated metrics** or performance statistics
- **No horizontal scrolling** on any viewport (all content within 1920px width)
- **Readable text** — all on-screen text must be legible in the recording

## Suggested Structure & Content

### 0:00–0:05 | Opening Title
**Visual**: Title card — "SAANS SAATHI AI — Every Breath Matters. Every Decision Counts."
**Narration**: "This is SAANS SAATHI AI — an urban air-quality and sustainable-living intelligence platform."

### 0:05–0:25 | Problem Introduction
**Visual**: Landing page — product identity "Every Breath Matters.Every Decision Counts."; seven module CTA links
**Narration**: "Urban air pollution is fragmented, technically inaccessible, and rarely translated into personalized guidance. Most platforms present model forecasts as live measurements without provenance. Families struggle to coordinate decisions across diverse health conditions and daily routines. SAANS SAATHI AI solves this with an integrated, privacy-conscious platform."

### 0:25–0:55 | Dashboard + Air Intelligence
**Visual**: Navigate to `/dashboard` → click "Air Intelligence" → `/air-quality` with location selected (e.g., Delhi)
**On-screen**:
- AQI value with CPCB banner (or "unavailable" with reason if no data)
- Pollutant concentrations: PM2.5, PM10, NO₂, SO₂, CO, O₃ with provider labels
- "model-based data" disclaimer where applicable
- Observation time and freshness timestamp
- AQI category table (Good 0-50, Satisfactory 51-100, etc.)
**Narration**: "The Air Intelligence module shows current air-quality detail. Notice the CPCB 2014 National AQI with pollutant concentrations. When data is unavailable, the system reports `status: unavailable` with the reason — no fabricated readings are ever displayed. Model-based forecast data is always labelled separately."

### 0:55–1:25 | Family Intelligence
**Visual**: Navigate to `/family` → health consent → household form (name: "Test Household", city: "New Delhi", lat: 28.6139, lon: 77.2090, timezone: "Asia/Kolkata") → save → view recommendations
**On-screen**:
- Session gate with health consent checkbox
- Household form fields
- Banner: "Anonymous session started. Create the household profile below."
- Recommendation history after saving
- "No account, no email. The backend stores only a hash of the token." (settings link)
**Narration**: "Family Intelligence enables anonymous household profiling. No account, no email required. The session is authenticated via a bearer token stored locally. Health flags are optional and add general precautions — they are not a diagnosis. Recommendations are generated based on the profile and activity preferences."

### 1:25–1:55 | SmartRoutine AI
**Visual**: Navigate to `/smart-routine` → add activity "Morning walk" (08:00, 30 min, outdoor, moderate) → add second activity → view "Your day" card
**On-screen**:
- Activity add form
- "Your day" card with activities ordered by start time
- "Timing guidance is not connected" advisory
- Up to 12 activities supported (oldest replaced)
**Narration**: "SmartRoutine AI is a deterministic daily scheduler. Activities are ordered by start time. Up to 12 are supported. The timing guidance advisory notes that exposure-aware scheduling needs current air-quality data. This planner stores your activities and never invents a recommendation."

### 1:55–2:25 | IndoorShield AI
**Visual**: Navigate to `/indoor-shield` → check 4/8 shelter checklist items → save → view recommendations
**On-screen**:
- 8-item shelter checklist with progress (4/8)
- "no indoor sensor data is claimed" banner
- Ventilation guidance: "Ventilate when outdoor PM2.5 is lowest, typically early morning in many Indian cities. This is general guidance, not a reading from a sensor in your home."
- Recommendation list after assessment
**Narration**: "IndoorShield AI assesses indoor environment basics. The 8-item shelter checklist covers key ventilation and air-exchange factors. Critically, no indoor sensor data is claimed — this is general guidance, not measurements from sensors in your home. All recommendations include appropriate disclaimers."

### 2:25–2:55 | EcoRoute AI
**Visual**: Navigate to `/eco-route` → select modes (walking, cycling) → 5km distance → view comparison
**On-screen**:
- Transport mode selectors (walking, cycling, car, bus, metro, two-wheeler)
- Emission factor labels: DEFRA 2023, IPCC 2006, CEA v22
- Comparison column with factor values and units
- "No route is drawn or scored on this device. Pollution exposure is only shown when the comparison service returns an exposure index built from real air-quality data; otherwise the column stays empty."
- Unsupported mode (e.g., bus without factor) shows empty column
**Narration**: "EcoRoute AI compares transportation modes for carbon impact. Emission factors are sourced from DEFRA 2023, IPCC 2006, and CEA v22. Unsupported modes return null — never invented numbers. No route is drawn or scored on this device. Pollution exposure is only shown when real air-quality data is available."

### 2:55–3:25 | Impact Intelligence
**Visual**: Navigate to `/impact` → log activity "walked" 5km today → view "Your log" → disclaimer
**On-screen**:
- Activity log entry (type: walked, quantity: 5km, date: today)
- "Amounts are the quantities you entered, not savings." disclaimer
- Factor provenance: DEFRA 2023, IPCC 2006, CEA v22 with source URLs, versions, retrieved_on
- "Baseline assumption: kilometres that would have been driven by car if the user had not walked or worked from home. Labelled as an assumption, not a measured baseline."
- Goals/trends summary with modelled baseline disclosure
**Narration**: "Impact Intelligence logs sustainability activities. The amounts entered are the quantities you provided — not computed savings. A baseline assumption is disclosed as such — kilometres that would have been driven by car if the user had not walked or worked from home. Labelled as an assumption, not a measured baseline. Emission factor provenance is always shown."

### 3:25–3:55 | SAANS AI Copilot
**Visual**: Navigate to `/copilot` → conversation UI with "No messages yet" → type question → send → caveat
**On-screen**:
- Conversation UI with placeholder "No messages yet"
- Question input field
- After send (Gemini unavailable): "When the service is unavailable, no answer is generated here"
- If Gemini were configured: grounded response citing FactPack data
**Narration**: "The SAANS AI Copilot provides grounded conversation. When the AI service is unavailable, the system clearly states that no answer is generated here — it always falls back to deterministic recommendations. When configured, Gemini responses cite application data facts and never invent measurements or diagnoses."

### 3:55–4:15 | Privacy & Data Persistence
**Visual**: Refresh browser (F5) → verify all data persists → bearer token in localStorage → activities in localStorage → profile data
**On-screen**:
- Post-refresh state
- Confirmation that all data persists across refresh
- Session state in database
- Activities retained in localStorage
**Narration**: "Data persists across browser refresh. All state is stored under an anonymous session — no user accounts, no personal information collected. The bearer token in localStorage maintains the session; activities and preferences in localStorage persist; profile data in the database persists."

### 4:15–4:30 | Closing
**Visual**: Title card — "SAANS SAATHI AI — Every Breath Matters. Every Decision Counts." + GitHub repo link + key principles
**Narration**: "SAANS SAATHI AI — converting environmental data into personalized, reliable decisions for everyday breathing. Every breath matters. Every decision counts."

---

## Recording Checklist

### Pre-Recording
- [ ] Backend running: `uvicorn app.main:app --port 8000 --loop app.core.loop:selector_loop_factory`
- [ ] Frontend running: `npm run dev` (with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in `.env.local`)
- [ ] All 11 routes verified: `curl -s http://localhost:3000/` through all routes return 200
- [ ] Console: 0 errors across all routes (F12 → Console tab)
- [ ] Network: 0 failed HTTP requests (status ≥ 400) across all routes
- [ ] Mobile viewport verified: Pixel 7 (390×850) via Playwright or Chrome dev tools
- [ ] No API keys in view anywhere in the application UI
- [ ] `.env.local` confirmed: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
- [ ] Background applications closed to avoid notification popups

### During Recording
- [ ] Show on-screen time visible (optional, for video editing)
- [ ] Cursor visible but not distracting; avoid rapid mouse movements
- [ ] Speak clearly at consistent volume; pace ~130-150 words/minute
- [ ] If stumbling, pause, recompose, and re-record that section
- [ ] If something unexpected happens (error, load), continue narration and note it; do not fabricate
- [ ] Keep recording going; it's better to have extra footage than to cut prematurely

### Post-Recording
- [ ] Trim to 3-5 minutes (remove any stumbles, pauses, or errors)
- [ ] Verify no API keys or sensitive data visible in any frame
- [ ] Verify no fabricated readings (AQI values, sensor data, savings) appear
- [ ] Verify all on-screen text is legible (zoom test at 75% and 100%)
- [ ] Add title card at start and closing card at end
- [ ] Export as MP4 (H.264 codec preferred) or WebM (VP9 codec)
- [ ] Upload to YouTube (unlisted) or Vimeo (private) for video hosting
- [ ] Obtain video URL for submission form

---

## Narration Script (Full)

> "This is SAANS SAATHI AI — an urban air-quality and sustainable-living intelligence platform. Every breath matters, every decision counts."

> "Urban air pollution is fragmented, technically inaccessible, and rarely translated into personalized guidance. Most platforms present model forecasts as live measurements without proper provenance. Families struggle to coordinate decisions across diverse health conditions and daily routines."

> "SAANS SAATHI AI solves this with an integrated, privacy-conscious platform that translates environmental information into personalized, actionable decisions for everyday breathing and living."

> "The Air Intelligence module shows detailed air-quality analysis. Here the CPCB 2014 National AQI with pollutant concentrations including PM2.5, PM10, NO2, SO2, CO, and O3. Notice the provider labels and observation timestamps. When data is unavailable, the system reports status unavailable with the reason — no fabricated readings are ever displayed. Model-based forecast data is always labelled separately."

> "The Family Intelligence module enables anonymous household profiling. No account, no email required. The session is authenticated via a bearer token stored locally. Health flags are optional and add general precautions to activity guidance — they are not a diagnosis or a medical assessment. Recommendations are generated based on the profile and activity preferences."

> "SmartRoutine AI is a deterministic daily scheduler. Activities are ordered by start time. Up to 12 activities are supported, with the oldest replaced when the limit is exceeded. The timing guidance advisory notes that exposure-aware scheduling needs current air-quality data. This planner stores your activities and never invents a recommendation."

> "IndoorShield AI assesses indoor environment basics. The 8-item shelter checklist covers key ventilation and air-exchange factors. Critically, no indoor sensor data is claimed — this is general guidance, not measurements from sensors in your home. All recommendations include appropriate disclaimers."

> "EcoRoute AI compares transportation modes for carbon impact. Emission factors are sourced from DEFRA 2023, IPCC 2006, and CEA v22. Unsupported modes return null — never invented numbers. No route is drawn or scored on this device. Pollution exposure is only shown when the comparison service returns an exposure index built from real air-quality data; otherwise the column stays empty."

> "Impact Intelligence logs sustainability activities. The amounts entered are the quantities you provided — not computed savings. A baseline assumption is disclosed as such — kilometres that would have been driven by car if the user had not walked or worked from home. Labelled as an assumption, not a measured baseline. Emission factor provenance is always shown."

> "The SAANS AI Copilot provides grounded conversation. When the AI service is unavailable, the system clearly states that no answer is generated here — it always falls back to deterministic recommendations. When configured, Gemini responses cite application data facts and never invent measurements or diagnoses."

> "Data persists across browser refresh. All state is stored under an anonymous session — no user accounts, no personal information collected. The bearer token in localStorage maintains the session; activities and preferences in localStorage persist; profile data in the database persists."

> "SAANS SAATHI AI — converting environmental data into personalized, reliable decisions for everyday breathing. Every breath matters. Every decision counts."

---

## Evidence Supporting This Demo

All features shown are verified from the Step 18 QA execution:

- ✅ All 11 routes render with 0 console errors and 0 failed HTTP requests in real Chromium
- ✅ 14 of 15 user workflows complete successfully (1 conditional: Copilot AI — documented caveat)
- ✅ Zero fabricated readings: CPCB unavailable honestly reported with `aqi_unavailable_reason`
- ✅ Model-forecast distinction: All model output labelled "model-based data"
- ✅ Emission factors sourced: DEFRA 2023, IPCC 2006, CEA v22; unsupported modes → null
- ✅ User-entered quantities: Impact log displays entered values, not computed savings
- ✅ Data persistence: Verified across browser refresh (workflow W15)
- ✅ WCAG 2.2 AA structure: Semantic HTML, ARIA labels, focus indicators, color contrast, skip links
- ✅ Session-scoped ownership: Anonymous bearer token; no accounts, no emails, no phone numbers
- ✅ Fail-closed AI: Gemini unavailable → "When the service is unavailable, no answer is generated here"
- ✅ All quality checks pass: Ruff, Black, MyPy, Bandit, pip-audit, ESLint, TypeScript, next build

---

## If Gemini API Key Is Obtained

If the demo is recorded after obtaining a Gemini API key, the Copilot scene would change:

**Visual**: After sending a question to the Copilot → grounded response citing FactPack data
**On-screen**: Conversation response with answer text + up to 5 action items with fact references + up to 3 avoid items with reason fact references
**Narration**: "When the Gemini service is configured, the Copilot provides grounded responses citing application data. For example, when asked about air quality for a morning walk, the response cites the current AQI, pollutant concentrations, and forecast data from the FactPack — never inventing measurements or diagnoses."

**Narration addition**: "When the AI service is configured, responses are grounded in the application's FactPack — a structured set of application data including current AQI values, pollutant concentrations, observation times, household profile, activity preferences, and emission factors. The model never independently calculates AQI (that's the deterministic backend's role), never invents sensor measurements, never invents emission factors, and never presents medical diagnoses."

---

## Important Notes

- **Do not display** any API keys, database credentials, or personal information in any frame
- **Do not fabricate** AQI values, sensor readings, or environmental savings if the service returns unavailable
- **Do not show** horizontal scrolling on any viewport (360×800 through 1920×1080)
- **Do not** use background music or sound effects that could interfere with narration
- **Do** ensure all on-screen text is legible in the final recording (test at recording resolution)
- **Do** mention the deterministic fallback when AI is unavailable — this is a key credibility feature
- **Do** highlight the privacy features — no account, no email, no personal information collected

---

*Demo script prepared as part of Step 19 — Final Release Preparation on 2026-11-22. Actual video recording and editing required. All features demonstrated are verified from the Step 18 QA execution.*