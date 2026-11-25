# Before-After Comparison — Step 30

## 1. Scope

This report compares the landing page before Step 30 (the original marketing page, as captured in the baseline screenshots and the original source code) against the Step 30 improved version (running at `http://localhost:3000/`). The comparison is visual + functional + structural. No environmental data was invented in either version.

## 2. Visual diff — high-level

| Aspect | Before (baseline) | After (Step 30) |
| --- | --- | --- |
| **Hero layout** | Single column on mobile, `1.05fr` / `0.95fr` on `lg`. Heading gradient used `accent-700` (missing token, caused TS error). | Two‑column layout on all breakpoints, `1.1fr` / `0.9fr` on `lg`. Gradient corrected to `from-brand-800 to-accent-600` (both tokens exist). |
| **Heading typography** | `text-4xl` / `sm:text-5xl` / `lg:text-[3.4rem]`. Gradient broken because `accent-700` undefined. | `text-5xl` / `sm:text-6xl` / `lg:text-[3.4rem]`. Gradient uses existing tokens. |
| **CTA positioning** | Both CTAs in a flex wrap gap‑3. | Primary CTA above secondary on mobile for better tap target; side‑by‑side on `lg`. |
| **Trust line** | Bottom of hero section. | Moved above the InterfacePreview card, keeping visual focus on identity + action. |
| **InterfacePreview** | Fixed relative width; three placeholder dots; 6 pollutant cards `px-2.5.py-2` (very narrow); provenance notice squeezed at bottom. | Full‑height card (`h-full`); placeholder text "No location selected" / "Model‑based data"; pollutant grid `sm:grid-cols-[auto_1fr]` (fluid 1‑3 columns); provenance banner below the grid, full width. |
| **CapabilityStrip** | Four badge items with descriptions that duplicated the ModulesSection. | Same four items, but descriptions refined to avoid redundancy; consistent token usage. |
| **ModulesSection** | Showed 9 nav items (allNavItems.filter) including Settings. | Shows exactly 7 modules (the 7 core destinations), matching the Step 30 brief. |
| **HowItWorks** | Four steps in an ol with `shadow-card` rounding. | Same 4 steps, but with refined rounding (`rounded-2xl.border.border-line.bg-white.p-5`) and better vertical rhythm. |
| **ProblemSection** | 3 problem cards with `shadow-card` rounding. | Same 3 problems, but with `p-6` padding and refined typography. |
| **StandardsSection** | CPCB 2014 AQI table + US/EU separation + category table. | Unchanged — already well‑structured and accurate. |
| **AccessibilitySection** | 4 commitments (keyboard, colour‑alone, responsive, privacy). | Unchanged — already comprehensive. |
| **CopilotSection** | Grounded questions, "Not connected" status, 3 boundaries. | Unchanged — already explicit about no Gemini in browser. |
| **FaqSection** | 6 accordion items (live, standard, source, privacy, key, mobile). | Unchanged — comprehensive for the build. |
| **CtaSection** | Gradient `bg-gradient-to-br from-brand-900 via-brand-800 to-accent-800`. | Same gradient (all 3 tokens exist) but with refined padding (`p-6` instead of `p-12`) and text‑white/90 opacity. |

## 3. Structural diff — before vs after

### Before (simplified page tree)

```
/ LandingPage
  / Hero (identity + CTA + InterfacePreview)
  / CapabilityStrip (4 badges)
  / ProblemSection (3 problems)
  / ModulesSection (9 nav items)
  / HowItWorks (4 steps)
  / StandardsSection (AQI + table)
  / AccessibilitySection (4 commitments)
  / CopilotSection (grounded questions)
  / FaqSection (6 accordion items)
  / CtaSection (gradient + 2 CTAs)
```

### After (Step 30 page tree)

```
/ LandingPage
  / Hero (identity + CTA + InterfacePreview, corrected gradient, better layout)
  / CapabilityStrip (4 refined badges)
  / ProblemSection (3 refined problems)
  / ModulesSection (7 core modules only)
  / HowItWorks (4 steps, refined rounding)
  / StandardsSection (AQI + table, unchanged)
  / AccessibilitySection (4 commitments, unchanged)
  / CopilotSection (grounded questions, unchanged)
  / FaqSection (6 accordion items, unchanged)
  / CtaSection (refined gradient + 2 CTAs)
```

### Navigation diff

- Before: Sidebar had 5 groups (OVERVIEW / PROTECTION / SUSTAINABILITY / ASSISTANT / WORKSPACE) + 9 items including Settings.
- After: Sidebar has the same 5 groups but the IA labels match the Step 29 updates (`Personal protection` / `Preferences`); ModulesSection on landing page now shows exactly 7 modules.

## 4. Functional diff — what changed under the hood

| Feature | Before | After |
| --- | --- | --- |
| Hero gradient | `from-brand-800 to-accent-700` (TS error: accent‑700 missing) | `from-brand-800 to-accent-600` (both tokens exist) |
| Hero layout ratio | `1.05fr` / `0.95fr` | `1.1fr` / `0.9fr` (better balance) |
| CTA stacking | Flex wrap gap‑3 (both on same row if room) | Primary above secondary on mobile; side‑by‑side on `lg` |
| InterfacePreview height | Auto (children determine) | `h-full` card forces full‑height layout |
| InterfacePreview placeholders | Three `.bg-slate-300` dots | "No location selected" + "Model‑based data" text |
| InterfacePreview pollutant grid | Fixed `px-2.5.py-2` cards, `—` + unit on same line | Fluid `sm:grid-cols-[auto_1fr]` cards, `—` on one line, unit on next |
| InterfacePreview provenance | Short 2‑sentence notice at bottom | Full‑width amber banner below grid, 4‑sentence explanation |
| ModulesSection item count | 9 items (allNavItems) | 7 items (core modules only) |
| CapabilityStrip redundancy | Descriptions duplicated elsewhere | Descriptions refined, no redundancy |
| Landing page TypeScript | Error: `accent-700` undefined | Clean (gradient corrected) |

## 5. What Was Preserved (not changed)

- All 11 routes remain functional with their original `h1` headings.
- Backend API contracts unchanged: `/healthz`, `/api/v1/air-quality/current`, CORS `Access-Control-Allow-Origin: http://localhost:3000`.
- All seven modules keep their data schemas, local storage keys and core behaviour.
- Emission factors are only those served by the Impact factor registry; no fabricated factors.
- No environmental data is ever invented; the landing page explicitly states "Interface preview · not live data".
- The constrained Copilot response schema is preserved; only `source===ai` may be labelled AI.
- ESLint, TypeScript, Vitest and production build are clean — no regressions introduced.
- The StandardsSection, AccessibilitySection, CopilotSection and FaqSection are unchanged (already accurate and well‑structured).

## 6. Verdict

The Step 30 landing page redesign delivers a visually balanced, modern entrance to the SAANS SAATHI AI platform. The hero gradient bug is fixed, the two‑column layout works at all breakpoints, the AQI preview is no longer cramped, the module list is correctly scoped to 7 core destinations, and TypeScript compiles cleanly. No environmental data is invented, no routes are broken, and all existing tests pass. The application remains running at `http://localhost:3000/`.