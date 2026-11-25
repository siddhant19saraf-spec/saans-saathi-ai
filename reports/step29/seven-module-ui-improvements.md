# Seven-Module UI Improvements — Step 29

Each module keeps its existing data contract and honesty rules. The work below is presentation,
interaction and clarity — no module gained a new calculation, and none was allowed to display a
number the backend does not supply.

---

## 1. Air Intelligence (`/air-quality`)

**Changed**

- `LocationSelector` added at the top of the page: type-ahead search over the bundled place list,
  autocomplete results with region labels, saved-place shortcuts, and a link to pick a point on the
  map. Selecting a result sets the active location; the page's existing query then re-runs.
- `AqiDial` and `SeverityBadge` pair every AQI value with the CPCB category name and its numeric
  range, so severity is never colour-only.
- `StandardsTable` and `ProviderHealthPanel` were restyled onto the new card/section rhythm without
  changing their content.
- Forecast section keeps its explicit unavailable state; the timezone contract was corrected so a
  `null` timezone from the forecast endpoint is accepted instead of breaking the page.
- Selected-location card shows coordinates, source and freshness alongside the search control.

**Preserved**

- CPCB as the primary index; US and European AQI shown separately with a "different scales" alert.
- Every provider panel carries source, observed time and attribution.
- No chart renders without a provider response.

**Honesty guardrail**

The search control selects a coordinate, not a monitoring station. The page continues to label
model data as model-based and never presents an interpolated surface as a measurement.

---

## 2. Family Intelligence (`/family`)

**Changed**

- A three-step indicator (`Household` → `Preferences` → `Recommendations`) now sits above the
  workflow. Each step shows a number, a check when complete, an `aria-current="step"` marker on the
  active step, and a one-line description of what it covers.
- Step state is derived from real data: profile present, preferences present, recommendation batch
  present. It is not a decorative progress bar.
- Profile summary, member list and recommendation cards were moved onto the shared card system with
  clearer section headers.

**Preserved**

- Anonymous session gate and session-scoped storage are unchanged.
- Consent is still explicit before health flags are stored; withdrawing consent and deleting the
  household remain available.
- Recommendations are still framed as general guidance, never a diagnosis.

**Honesty guardrail**

The step indicator reflects stored state only. A household with no members does not show a
"complete" badge for a step that has no data.

---

## 3. SmartRoutine (`/smart-routine`)

**Changed**

- Summary metrics above the planner: number of activities, total planned minutes, and the first
  scheduled activity.
- Visual timeline: each activity is a card on a vertical rail with start time, duration, venue,
  intensity and a fixed/flexible indicator.
- Inline edit → save → cancel per activity, using the existing `update` action exposed by
  `useRoutineActivities`.
- Overlap detection across the whole plan, including activities that cross midnight. Conflicting
  pairs are listed in a warning panel, and the affected cards get an amber border and an
  "Overlaps another activity" label — text, not colour alone.
- Time inputs are typed `time` with 15–180 minute duration bounds and inline validation.
- The timezone note now names the household timezone when one is known and states that times are
  wall-clock times, so a user in another timezone is not misled.

**Preserved**

- Deterministic scheduling logic; no AI is used to place activities.
- Local-only storage of the plan.
- Delete and add flows keep their existing confirmation and validation behaviour.

**Honesty guardrail**

Conflict warnings describe overlap only. They do not claim a pollution exposure difference between
two time slots.

---

## 4. IndoorShield (`/indoor-shield`)

**Changed**

- A persistent `Self-reported actions, not a measurement` badge in the page header, plus a sentence
  in the description: checking an item records your own action, not indoor air quality.
- Overall completion `Progress` with an accessible label, followed by per-category cards
  (ventilation, dust, kitchen, filtration) each with its own count, percentage and progress bar.
- Category hints explain what the group covers.
- Mobile: checklist rows are full-width tap targets with the checkbox first and no horizontal
  overflow at 320 px.

**Preserved**

- The checklist schema, categories and local persistence are unchanged.
- Guidance remains general and non-medical.

**Honesty guardrail**

There is no sensor input anywhere in this module, and the interface says so on the page rather than
only in a footnote.

---

## 5. EcoRoute (`/eco-route`)

**Changed**

- Origin/destination header after a comparison: origin label → destination label, with an
  "Estimated route" / "Provider route" badge.
- Three comparison cards above the existing table: **Lower carbon**, **Lower exposure** and
  **Faster**, populated from the response's `recommended_for` arrays. When a dimension has no
  recommendation the card says "Not ranked" instead of inventing a winner.
- Distance and duration chips, plus "Estimated by" vs "Routing via" wording that depends on the
  response's `is_estimate` flag.
- Loading, empty and error states kept and restyled; form validation messages remain inline.

**Preserved**

- The comparison `<table>` and its exact strings (`Car`, `Cycling`, `1.6 kg`, `78 / 100`,
  `Not reported`) are untouched — the new cards wrap the table, they do not replace it.
- Emission factors are only those served by the backend registry.
- Route exposure is only claimed when the response supplies it.

**Honesty guardrail**

"Not ranked" is a first-class state. A mode with no factor is never assigned one, and a mode with
no exposure figure is never given a score.

---

## 6. Impact Intelligence (`/impact`)

**Changed**

- KPI strip at the top: number of entries, number of activity types, the log window in days and the
  number of registered emission factors. Each KPI shows an empty label when the underlying value is
  absent.
- Activity logging form keeps category, quantity and unit inputs, with units shown next to the
  field and in the history.
- History list shows quantity + unit + date per entry, with removal.
- A "Units and method" card explains, per activity type, what the quantity means and what unit is
  stored, and states that a CO₂e total would require the server to apply a versioned factor — the
  browser never multiplies the two.
- Factor registry panel lists key, label, value, unit, source, source URL, version and retrieval
  date, with its own loading/error/unavailable states.

**Preserved**

- Local activity log and its storage key.
- No export was added, because the existing backend does not expose one.
- No carbon saving is computed or displayed.

**Honesty guardrail**

The page is deliberately explicit that quantities are not savings. Empty states read "No entries
yet" rather than showing `0` as if a measurement had been taken.

---

## 7. SAANS AI Copilot (`/copilot`)

**Changed**

- Premium chat surface: introduction card, suggested question chips, message list with user and
  assistant styling, and a composer with a clear disabled/busy state.
- Every answer is labelled by its actual source:
  - `AI-generated, grounded` (with the model name when the response provides one)
  - `Deterministic rules answer`
  - `Deterministic fallback`
- Non-AI answers carry an explanatory sentence: either "composed by the deterministic rules engine
  from the cited facts" or, for fallback, "the language model was unavailable … It is not a Gemini
  response."
- Citations render source, observation time and value.
- A sidebar card explains the two modes and links to data sources in Settings.
- Graceful error state with retry when the request fails; no partial or invented answer is shown.

**Preserved**

- The constrained response schema is unchanged.
- Gemini never overrides deterministic calculations; it only phrases grounded facts.
- The deterministic fallback remains functional with no model key.

**Honesty guardrail**

The label is driven by the response's `source` field, not by optimism. Only `source === "ai"` may be
described as AI-generated.

---

## Cross-module consistency

| Concern | Shared treatment |
| --- | --- |
| Page intro | `PageHeader` with eyebrow, title, description and actions |
| Section framing | `SectionHeader` + `Card` |
| Loading | `Skeleton` with `aria-busy` and a polite live region |
| Error | `DataState` with message and Retry |
| Empty | `EmptyState` or `MetricCard` empty label, always with a next step |
| Tables | `ResponsiveDataTable` with a real caption and an internal scroll frame, so wide tables never widen the page |
| Destructive actions | `ConfirmDialog` or a two-step confirm button |
| Confirmation feedback | `useToast` polite live region |
| Focus | One visible ring token across buttons, links, inputs and cards |
