# Design System Improvements — Step 29

## 1. Goal

Replace an ad-hoc set of page-local styles with one token set and one component vocabulary, so that
every route reads as the same product without duplicating components. The system is implemented in
Tailwind CSS v4: tokens live in the `@theme` block of `frontend/src/app/globals.css` and are consumed
directly as utilities (`bg-surface`, `text-ink-muted`, `border-line`). There is no
`tailwind.config.ts` in this project and none was added.

## 2. Colour tokens

### Surfaces and text

| Token | Value | Role |
| --- | --- | --- |
| `--color-canvas` | `#f5f8f4` | App background; faint green-tinted off-white |
| `--color-surface` | `#ffffff` | Cards, dialogs, inputs |
| `--color-surface-muted` | `#f1f6f1` | Nested blocks, table headers, subtle panels |
| `--color-surface-raised` | `#fbfdfb` | Gradient endpoint for hero surfaces |
| `--color-line` | `#e2e9e2` | Hairline borders and dividers |
| `--color-line-strong` | `#cfdad1` | Scrollbar thumb, emphasised dividers |
| `--color-ink` | `#0b2018` | Primary text |
| `--color-ink-muted` | `#53655c` | Secondary text, descriptions |
| `--color-ink-subtle` | `#788a80` | Tertiary text, captions, metadata |

### Brand scale (deep forest green)

`brand-50 #eff8f3` · `100 #d9eee2` · `200 #b5ddc8` · `300 #86c5a9` · `400 #52a685` ·
`500 #2f8a6a` · `600 #1f7057` · `700 #195c48` (primary action) · `800 #154a3b` ·
`900 #123d31` · `950 #08271f`

### Accent scale (emerald, reserved)

`accent-50 #ecfdf5` … `accent-500 #10b981` … `accent-950 #022c22`. Accent is used only for positive
or "live" signals and the hero glow; it never replaces the brand green for actions.

### Severity scale (CPCB categories)

Six paired sets, each with background, foreground and border tokens:
`severity-good` `#e7f7ee / #0b5d3b / #b7e4c9`, `severity-satisfactory` `#f2f8df / #45611a / #d5e6a7`,
`severity-moderate` `#fdf3d7 / #6b4a06 / #f2d98a`, `severity-poor` `#fde8d7 / #7c3a0d / #f5c49b`,
`severity-very-poor` `#fde2e1 / #8a1f1c / #f6b3b1`, `severity-severe` `#f0e4fb / #4a1a6b / #d9bff2`.

Severity colour is always paired with the category name, a range and an icon, so AQI is never
communicated by colour alone.

## 3. Typography

- Single family: Inter via `--font-sans`, with `cv02/cv03/cv04/cv11` feature settings and
  `optimizeLegibility`.
- Scale in use: `text-[11px]` metadata · `text-xs` (12 px) captions · `text-sm` (14 px) body ·
  `text-base` (16 px) card titles · `text-lg`/`text-xl` section leads · `text-2xl`–`text-4xl`
  metrics and page titles.
- Headings use `text-wrap: balance`; paragraphs use `text-wrap: pretty` to avoid orphan lines.
- Metric values use `font-variant-numeric: tabular-nums` with `-0.02em` tracking (`metric-value`
  utility) so numbers align across cards.
- Hierarchy is carried by size, weight and ink level together — not by colour alone.

## 4. Spacing, radius, elevation

| Property | Scale |
| --- | --- |
| Spacing | 4 px base; page sections `space-y-9`; card padding `px-5 py-4/5`; grid gaps `gap-3`–`gap-6` |
| Radius | `rounded-lg` (8 px) controls · `rounded-xl` (12 px) nested blocks · `rounded-2xl` (16 px) cards · `rounded-full` pills |
| Shadows | `shadow-card` (`0 1px 2px rgb(8 39 31/.04), 0 10px 28px -22px rgb(8 39 31/.28)`) · `shadow-raised` for hover/dialog · `shadow-inset` for inset highlights |
| Max page width | `max-w-7xl` content column with responsive gutters |

Shadows are deliberately low-contrast: separation comes primarily from the border and the canvas
tint, which keeps dense screens calm.

## 5. Component inventory

### New in Step 29

| Component | File | Purpose |
| --- | --- | --- |
| `SectionHeader` | `ui/section-header.tsx` | Title + description + optional action, one rhythm for all sections |
| `StatusBadge` | `ui/status-badge.tsx` | Tone-based status with icon, used for live/stale/empty states |
| `MetricCard` | `ui/metric-card.tsx` | Label, tabular value, unit, hint, optional link; renders an explicit empty label instead of `0` when no value exists |
| `ChartContainer` | `ui/chart-container.tsx` | Titled chart frame with caption, height control and empty/error slot |
| `SearchInput` | `ui/search-input.tsx` | Consistent search field with icon and clear affordance |
| `ConfirmDialog` | `ui/confirm-dialog.tsx` | Accessible destructive confirmation (focus trap, labelled actions) |
| `ToastProvider` / `useToast` | `ui/toast.tsx` | Non-blocking confirmations with polite live region and dismiss |
| `ResponsiveDataTable` | `ui/responsive-data-table.tsx` | Scrollable table frame with a real `<caption>`, a thin scrollbar and a 34 rem minimum width so columns stay readable; the frame scrolls rather than pushing the page wider |
| `LocationSelector` | `navigation/location-selector.tsx` | Search, autocomplete, saved places and map link in one control |
| `MotionPreference` | `layout/motion-preference.tsx` | Applies the stored reduce-motion flag before paint |
| `useMounted` | `lib/use-mounted.ts` | Hydration-safe "is mounted" via `useSyncExternalStore`; avoids effect-driven setState |

### Existing components upgraded

`Card` (two-level surface + `shadow-card`), `Button` (six variants, four sizes, consistent focus
ring), `Badge`, `Alert`, `Switch`, `Checkbox`, `Field`, `Tabs`, `Accordion`, `Popover`,
`DropdownMenu`, `Dialog`, `Skeleton`, `Separator`, `Progress`, `EmptyState`, `DataState`,
`PageHeader`, `Breadcrumbs`.

### Deliberate non-duplication

The brief listed a `DashboardCard`. Rather than add a near-copy of `Card`, the dashboard uses `Card`
as the container and `MetricCard` as the dashboard-specific metric surface. `LoadingState`,
`ErrorState` and `EmptyState` are expressed through `Skeleton`, `DataState` and `EmptyState` instead
of three parallel components. This keeps one implementation per concept, as Phase 1 requires.

## 6. Status indicators

Three layers, each with a different job:

1. **Severity badge** (`severity-badge.tsx`) — CPCB category, always shows the label and range.
2. **Status badge** (`status-badge.tsx`) — data lifecycle: live, within window, stale, unavailable,
   estimate, preference-only.
3. **Inline alert** (`alert.tsx`) — explanations that must not be missed, e.g. "US and European AQI
   values use different breakpoints and are not comparable to CPCB".

## 7. Motion

- Tokens: `fade-in` 220 ms, `slide-up` 260 ms `cubic-bezier(.22,1,.36,1)`, `toast-in` 220 ms,
  accordion 180 ms.
- `card-lift` transitions only `box-shadow`, `border-color` and `transform`, at 180 ms.
- Two independent off-switches: the OS `prefers-reduced-motion` media query and an in-app
  `[data-reduce-motion="true"]` attribute written by the Accessibility settings toggle. Both collapse
  animation and transition durations to `0.01ms` and disable smooth scrolling.
- No animation gates a workflow: skeletons are replaced by content, not by a timed transition.

## 8. Verification

- `npx tsc --noEmit` — clean.
- `npx eslint src --max-warnings=0` — clean.
- `npx vitest run` — 149 tests across 28 files pass.
- `npm run build` — production build succeeds; all 11 routes prerender.
- Token usage is enforced by construction: no page introduces raw hex colours for surfaces, text or
  borders; severity and brand colours come from tokens.
