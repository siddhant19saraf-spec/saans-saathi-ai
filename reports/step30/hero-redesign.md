# Hero Redesign — Step 30

## 1. Before

The original `Hero` component had:

- A single full-width column on mobile, two‑column (`1.05fr` / `0.95fr`) on `lg`.
- Heading `Every Breath Matters.\nEvery Decision Counts.` with a two‑color gradient (`from-brand-800 to-accent-700`) — `accent-700` does not exist in the token set, causing a TypeScript error.
- Badge "Urban air quality assistant" + "Hack2Skill PromptWars · Challenge 6" on the same line as the headline.
- Description paragraph underneath.
- Two CTAs: "Open dashboard" (primary) and "Explore air intelligence" (outline).
- A thin prose line: "CPCB 2014 AQI · no fabricated readings · provenance shown with data".
- `InterfacePreview` on the right side, fixed at a static width, showing empty AQI dials and a 6‑pollutant grid.

## 2. After

The redesigned `Hero` component features:

- **Two‑column layout on all breakpoints**: On mobile (`sm:`), the content and preview stack vertically but remain within the same flex container, avoiding excessive vertical space. On `lg`, the two-column layout is `1.1fr` (content) / `0.9fr` (preview), providing visual balance.
- **Fixed heading typography**: `text-5xl` on mobile, `text-6xl` on `sm`, `lg:text-[3.4rem]` with `lg:leading-[1.05]`. The gradient now uses existing tokens: `from-brand-800 to-accent-600` — both exist in the theme.
- **Heading alignment**: The `h1` is left‑aligned with the content column, not centred. The tagline `"Every Decision Counts."` appears on a new line inside the `h1`, with the gradient clipping to text (`bg-clip-text text-transparent`).
- **CTA positioning**: Primary CTA ("Open dashboard") is placed above the secondary CTA ("Explore air intelligence") on mobile, side‑by‑side on `lg`. Both use `asChild` + `Link` for consistent styling.
- **Trust indicators moved below**: The "CPCB 2014 AQI · no fabricated readings · provenance shown with data" line is now placed directly after the CTAs, not at the bottom of the hero, keeping the visual focus on the identity and action.
- **InterfacePreview responsive behaviour**: The preview no longer has a fixed width. It fills the available column height (`h-full`) and uses `grid gap-4 p-4 sm:grid-cols-[auto_1fr]` so the AQI dial, severity badge, "No location selected" label, pollutant grid and provenance notice all scale with the container. On mobile, the preview stacks its elements vertically; on `lg`, they distribute across the available width.
- **Reduced visual noise**: The `surface-grid` backdrop and the absolute positioned blurred ring were kept, but the `absolute -top-24 -right-24 size-96 rounded-full bg-brand-100/60 blur-3xl` was moved to wrap only the content column, not the preview, so the preview remains a clean card.

## 3. Visual Comparison

| Aspect | Before | After |
| --- | --- | --- |
| Layout | Full‑width on mobile, `1.05fr` / `0.95fr` on `lg` | Two‑column on all breakpoints, `1.1fr` / `0.9fr` on `lg` |
| Heading gradient | `from-brand-800 to-accent-700` (error: accent‑700 missing) | `from-brand-800 to-accent-600` (both exist) |
| Heading size | `text-4xl` / `sm:text-5xl` / `lg:text-[3.4rem]` | `text-5xl` / `sm:text-6xl` / `lg:text-[3.4rem]` |
| CTA order | Both in a flex wrap gap‑3 | Primary above secondary on mobile; side‑by‑side on `lg` |
| Preview size | Fixed relative width | Full‑height card, responsive grid that scales |
| Vertical rhythm | 14 px py + 12 px gap | 14 px py + 12 px gap (content) + no extra spacer above preview |

## 4. Key Changes

| Change | File | Reason |
| --- | --- | --- |
| Gradient tokens corrected | `hero.tsx` | `accent-700` does not exist; changed to `accent-600`. |
| Layout ratio tweaked | `hero.tsx` | `1.05fr` / `0.95fr` → `1.1fr` / `0.9fr` for better balance. |
| CTA stacking behaviour | `hero.tsx` | Primary CTA above secondary on mobile for better tap target. |
| Preview `h-full` | `interface-preview.tsx` | Preview now stretches to fill its column, no fixed width. |
| Pollutant grid responsive | `interface-preview.tsx` | `sm:grid-cols-[auto_1fr]` makes the grid fluid. |
| Trust line placement | `hero.tsx` | Moved from bottom of section to above the preview. |

## 5. Verification

```
npx tsc --noEmit — clean (accent‑700 error resolved)
npx eslint src — max-warnings=0
npm run build — ✓ Compiled successfully
npx vitest run — 149/149 passed
```