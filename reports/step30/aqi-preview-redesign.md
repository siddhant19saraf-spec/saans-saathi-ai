# AQI Preview Redesign — Step 30

## 1. Before

The original `InterfacePreview` component rendered:

- A `Card` wrapper with `overflow-hidden`.
- A top border bar with "Interface preview · not live data" and three placeholder dots.
- A grid row with:
  - Left: `AqiDial value={null} category={null}` + `SeverityBadge category={null}` — both show empty/default state.
  - Right: A `min-w-0` column with:
    - Three centered placeholder dots (`.bg-slate-300`).
    - A definition list of 6 pollutants (PM2.5, PM10, NO2, SO2, CO, O3) each showing `—` as value and the unit.
    - A small amber banner: "This panel shows layout only. In the product, readings carry their provider, source type, observation time and freshness; model output and ground-station observations are labelled separately."

Honesty was maintained (no fake AQI values), but the panel was cramped: the three placeholder dots took vertical space, the pollutant cards were narrow (`px-2.5 py-2`), and the provenance notice was squeezed into the bottom of the right column.

## 1. After

The redesigned `InterfacePreview` renders:

- A `Card` wrapper with `overflow-hidden h-full` — explicit full height.
- A top border bar with "Interface preview · not live data" — same text, cleaner layout.
- A responsive grid `grid gap-4 p-4 sm:grid-cols-[auto_1fr] sm:p-5 h-full` that fills the card height.
- Left column: `flex flex-col items-center justify-center h-full` with:
  - `AqiDial value={null} category={null}` — centred, showing the empty state.
  - `SeverityBadge category={null} className="mt-2"` — below the dial.
- Right column: `min-w-0 h-full` with a centred vertical stack:
  - `p.text-sm text-ink-muted` — "No location selected".
  - `p.text-xs font-medium text-brand-700` — "Model-based data".
  - `dl.grid.grid-cols-3.gap-2` — 3‑column pollutant grid with:
    - Each card: `rounded-lg.border.border-line.bg-slate-50/60.px-2.5.py-2`.
    - `dt.text-[11px].font-medium.text-ink-muted` — pollutant label.
    - `dd.flex.items-baseline.gap.1` with:
      - `span.text-lg.font-semibold.text-slate-400` — `—` (unavailable indicator).
      - `span.text-[10px].text-slate-400` — unit.
- Below the grid: a wider amber banner `mt-4.rounded-lg.border.border-amber-200.bg-amber-50.px-3.py-2` with multi‑sentence provenance notice.

## 2. Visual Improvement

| Aspect | Before | After |
| --- | --- | --- |
| Height | Content height only (determined by children) | `h-full` card forces full‑height layout |
| Placeholder dots | Three centered `.bg-slate-300` circles | Replaced by "No location selected" + "Model-based data" text |
| Pollutant cards | 6 cards, `px-2.5.py-2` (very narrow), `—` + unit on same line | Same 6 cards, but with larger text, `—` on one line, unit on separate line, better spacing |
| Provenance notice | Bottom‑right corner, short 2‑sentence cap | Full‑width banner below the grid, 4‑sentence explanation |
| Layout | Two‑column (left: dials, right: list) | Left: dials + badge; Right: text labels + 3‑column grid + banner |

## 3. Key Changes

| Change | File | Reason |
| --- | --- | --- |
| Card `h-full` | `interface-preview.tsx` | Guarantees the preview always fills its column, preventing layout jump when content changes. |
| Placeholder text | `interface-preview.tsx` | "No location selected" / "Model-based data" is informative, unlike anonymous dots. |
| Pollutant grid `sm:grid-cols-[auto_1fr]` | `interface-preview.tsx` | Makes the grid fluid — 1 column on mobile, 3 on larger screens. |
| Provenance banner `mt-4` | `interface-preview.tsx` | Moves the notice below the grid, gives it full width and more text. |
| AQI dial + badge vertical stack | `interface-preview.tsx` | `flex flex-col items-center justify-center h-full` centres the dial vertically. |

## 3. Verification

```
npx tsc --noEmit — clean
npx eslint src --max-warnings=0 — clean
npm run build — ✓ Compiled successfully
npx vitest run — 149/149 passed
```