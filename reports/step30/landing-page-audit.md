# Landing Page Audit — Step 30

## 1. Current State

The landing page at `/` (route-group `marketing`) composes 12 sections in order:

```
Hero
CapabilityStrip
ProblemSection
ModulesSection
HowItWorks
StandardsSection
AccessibilitySection
CopilotSection
FaqSection
CtaSection
```

All sections share the same visual design tokens (forest green, emerald, off-white, neutral grays, restrained shadows) and the same responsive grid (`max-w-6xl`, `px-4 sm:px-6 lg:px-8`). The page is static (no dynamic data) and serves as the marketing/awareness entry point before the 11 functional routes.

## 2. Component Inventory

| Component | File | Purpose |
| --- | --- | --- |
| `Hero` | `marketing/hero.tsx` | Identity, tagline, two CTAs, InterfacePreview |
| `CapabilityStrip` | `marketing/capability-strip.tsx` | Four principle badges (no fabricated readings, source-aware, location control, accessible by default) |
| `ProblemSection` | `marketing/problem-section.tsx` | Three problem statements (place/hour, households differ, claims need evidence) |
| `ModulesSection` | `marketing/modules-section.tsx` | 9 nav-item modules with status badges (Workspace, Needs data service, OpenStreetMap, Local profile, Local planner, Guidance checklist, Needs routing service, Local log, Needs AI service) |
| `HowItWorks` | `marketing/how-it-works.tsx` | Four-step workflow + evidence-attached advice div |
| `StandardsSection` | `marketing/standards-section.tsx` | CPCB 2014 AQI + US/EU separation + category table |
| `AccessibilitySection` | `marketing/accessibility-section.tsx` | Four commitments (keyboard first, never colour alone, responsive by design, session-based privacy) |
| `CopilotSection` | `marketing/copilot-section.tsx` | Grounded questions, not guessing game; status badge "Not connected"; three boundaries |
| `FaqSection` | `marketing/faq-section.tsx` | 6 Accordion items (live, standard, source, privacy, key, mobile) |
| `CtaSection` | `marketing/cta-section.tsx` | Gradient background, "Start with your location" headline, two CTAs |
| `InterfacePreview` | `marketing/interface-preview.tsx` | Static AQI dial + severity badge + "No location selected" + 6 pollutant cards + provenance notice |

## 3. Honesty Assessment

- No environmental data is fabricated anywhere on the landing page.
- The `InterfacePreview` explicitly states "Interface preview · not live data" and renders `null` values for AQI/dial.
- All CapabilityStrip descriptions state what the build does *not* do (no sample values, no mixed scales).
- The CopilotSection boundaries explicitly state "No Gemini key in browser code" and "No simulated replies".
- The CTA section's copy keeps the reader informed about connected vs. local state.

## 4. Pre‑Step 30 Issues (identified for Step 30 improvement)

| Issue | Location | Impact |
| --- | --- | --- |
| Hero heading gradient uses `bg-gradient-to-r from-brand-800 to-accent-700` — `accent-700` does not exist in the token set (only `accent-50`–`accent-950` are defined). | `hero.tsx` | Minor CSS error; will be corrected in redesign. |
| InterfacePreview pollutant grid uses `pollutantMeta.slice(0, 6)` — the slice depends on the severityMeta order, which may change. | `interface-preview.tsx` | fragile but functional. |
| CapabilityStrip items hard‑code descriptions that duplicate the seven‑module section. | `capability-strip.tsx` | Redundant but not incorrect. |
| ModulesSection shows 9 items (including Settings via `allNavItems.filter`) but the Step 30 brief asks for 7 modules. | `modules-section.tsx` | Will be corrected to show exactly 7. |
| CTASection gradient uses `bg-gradient-to-br from-brand-900 via-brand-800 to-accent-800` — all three tokens exist. | `cta-section.tsx` | OK. |
| FaqSection has 6 accordion items — comprehensive for the build. | `faq-section.tsx` | OK. |

## 5. Redirection

The landing page is the entry point. All CTAs navigate to the 11 functional routes. No dead links. The page does not claim live data; the `InterfacePreview` makes this explicit.

## 5. Verification

```
npx tsc --noEmit — clean
npx eslint src --max-warnings=0 — clean
npm run build — ✓ Compiled successfully
npx vitest run — 149/149 passed
```