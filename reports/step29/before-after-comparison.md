# Before-After Comparison — Step 29

## 1. Scope

This report compares the website before Step 29 (the baseline, captured in `step29-before/` screenshots) against the Step 29 improved version (running at `http://localhost:3000/`). The comparison is visual + functional + structural. No environmental data was invented in either version; the "before" screenshots show the original UI, and the "after" shows the transformed UI.

## 2. Visual diff — high-level

| Aspect | Before (baseline) | After (Step 29) |
| --- | --- | --- |
| **Canvas** | White background, no tint, no system‑reduced‑motion support | Soft off‑white `#f5f8f4` with a 10 % green‑tint; `[data-reduce-motion="true"]` collapses all motion |
| **Primary colour** | Ad‑hoc green for buttons, no systematic scale | Deep forest‑green scale `brand-50` → `brand-950`; emerald `accent-50` → `accent-950` reserved for highlights |
| **Surfaces** | One card weight everywhere; no shadow hierarchy | Three‑level surface system: `surface-hero` (hero glow), `surface` (cards), `surface-muted` (nested blocks) |
| **Charts** | Full‑bleed, no caption, no empty/error state | Wrapped in `ChartContainer` with title, caption, empty/error slot; tabular metric values; `minWidth(0)` for container-driven sizing |
| **Sidebar** | 5 groups: `OVERVIEW / PROTECTION / SUSTAINABILITY / ASSISTANT / WORKSPACE`; flat list, no collapse | 5 groups: `WORKSPACE / PERSONAL PROTECTION / SUSTAINABILITY / ASSISTANCE / PREFERENCES`; collapsible with persisted state, active rail, tooltips |
| **Map** | Grey rectangle when tiles don’t paint instantly | Tile-status overlay, `MutationObserver` + `requestAnimationFrame` watcher, explicit `© OpenStreetMap` attribution, `Open this area on OpenStreetMap` link |
| **Dashboard** | Five sparse panels; no welcome; large empty void when no location | 12 sections: welcome hero, location, AQI, pollutants, freshness, provenance, family readiness, routine, indoor, impact, quick actions, recent activity; tight 36 px section rhythm |
| **AQI display** | Colour‑only severity badge; no category name or range | `SeverityBadge` with category label + numeric range + icon; colour never the only signal |
| **Family steps** | Not present | 4‑step indicator: `Session → Household → Preferences → Recommendations`; done/current/aria-current markers |
| **SmartRoutine** | Plain list of activities, no timeline, no conflict warnings | Visual timeline rail, overlap conflict warnings (amber border + text), timezone‑labelled wall-clock note |
| **IndoorShield** | Checklist, no disclaimer | `Self-reported actions, not a measurement` badge; per-category progress bars; clear assessment‑vs‑measurement distinction |
| **EcoRoute** | Table only, no summary cards | Three comparison cards (Lower carbon, Lower exposure, Faster) above the table; "Not ranked" when no recommendation |
| **Impact** | Table of entries, no KPI strip, no units/method card | KPI strip (entries, types, factors); "Units and method" card exposing per‑type quantities and units; honest accounting badge |
| **Copilot** | Chat area, no source labels | Source‑labelled answers: `AI-generated, grounded` / `Deterministic rules answer` / `Deterministic fallback`; explicit fallback explanation; two‑mode sidebar card |
| **Settings** | One section with ad‑hoc groups | Six sections: Notifications, Data sources, Local data, Privacy, Preferences, Accessibility; reduce‑motion toggle; two‑step Clear controls |
| **Responsive** | Fixed widths; some routes overflowed below 600 px | All 11 routes at 10 viewport widths (320–1920 px); `ResponsiveDataTable` scroll frame; mobile drawer; collapsible sidebar |
| **Motion** | No reduced‑motion preference | `useMotionPreference()` + `prefers-reduced-motion`; `[data-reduce-motion="true"]` collapses all animation durations to 0.01 ms |

## 3. Structural diff — before vs after

### Before (simplified page tree)

```
/ dashboard
  / Current conditions (card)
  / Pollutant bar chart
  / Source & freshness
  / Trends & forecast
  / Personalised insights
  / Smart actions
```

### After (Step 29 page tree)

```
/ dashboard
  / DashboardHero (welcome + location + live AQI + freshness + provenance)
  / QuickActions (4 task buttons)
  / CurrentAirSection (AQI dial + pollutant grid + provider + provenance)
  / DailyPulse (family readiness · routine · indoor · impact metrics)
  / RecentActivity (latest 3 routine + 3 impact entries)
  / AnalyticsSection (trends & forecast, provider‑only)
  / InsightsPanel (household context + next actions)
```

### Before (navigation)

```
/ sidebar with 5 groups (OVERVIEW/PROTECTION/SUSTAINABILITY/ASSISTANT/WORKSPACE)
  fixed width, no collapse, no mobile drawer
```

### After (navigation)

```
/ sidebar with 5 groups (WORKSPACE/PERSONAL PROTECTION/SUSTAINABILITY/ASSISTANCE/PREFERENCES)
  collapsible (76 px / 280 px), persists in localStorage, active rail,
  mobile drawer (Radix Dialog), keyboard accessible (Ctrl+K, Tab order)
```

## 4. Functional diff — what changed under the hood

| Feature | Before | After |
| --- | --- | --- |
| Map tile loading | Spinner may stick forever (no watcher) | `TileStatusWatcher` resolves after 9 tiles finish + MutationObserver re‑check |
| Collapse persistence | Not available | `localStorage` + `useSyncExternalStore` module-level store; hydration‑safe |
| Reduce‑motion | Not supported | `useMotionPreference()` + OS query + `[data-reduce-motion="true"]` attribute |
| Nav IA | `Protection` / `Workspace` group labels | `Personal protection` / `Preferences` (intentional, two test expectations updated) |
| AQI severity | Colour only + badge | Category name + numeric range + icon + badge; colour never only signal |
| Family steps | N/A | 4‑step indicator with done/current/aria-current; derived from real data |
| SmartRoutine conflicts | No inline warning | Overlap detection + amber border + "Overlaps another activity" label |
| IndoorShield disclaimer | None | `Self-reported actions, not a measurement` banner + per-category progress |
| EcoRoute summary | Table only | Three comparison cards + table; "Not ranked" when no data; emission factors from registry only |
| Impact accounting | Table of entries, no totals | KPI strip + units/method table + explicit statement: browser never multiplies factors; no "kg saved" badge |
| Copilot source labels | None | `AI-generated, grounded` / `Deterministic rules answer` / `Deterministic fallback`; only `source===ai` may say AI |
| Settings structure | Ad‑hoc groups | Six labelled sections with anchor navigation; per‑store counts + Clear buttons; reduce‑motion toggle |
| Form Clear controls | Single‑click destructive | Two-step arm-then-confirm (armed 5 s, then performs or disarms) |
| Chart container | No min‑width constraint | `minWidth(0)` + `min-height: 0` so containers shrink with parent row |
| Section rhythm | Varied vertical spacing | Consistent `space-y-9` between top‑level sections; `space-y-3` / `space-y-4` inside |

## 5. Before‑after screenshot summary

| Screenshot file | Route | Description |
| --- | --- | --- |
| `dashboard-1440.png` (before) | `/dashboard` | Empty workspace, five sparse panels, large void |
| `dashboard-1440.png` (after) | `/dashboard` | Hero, quick actions, current air, daily pulse, recent activity — all populated |
| `map-1440.png` (before) | `/map` | Grey rectangle, no overlay, no attribution |
| `map-1440.png` (after) | `/map` | 9 OSM tiles loaded, active-place marker, tile-status overlay, attribution link |
| `family-1440.png` (before) | `/family` | Session gate + profile form, no step indicator |
| `family-1440.png` (after) | `/family` | Step indicator (Session → Household → Preferences → Recommendations), profile form + household form |
| `settings-1440.png` (before) | `/settings` | One section, no clear controls |
| `settings-1440.png` (after) | `/settings` | Six sections, reduce‑motion toggle, per‑store counts, two‑step Clear |
| `smart-routine-1440.png` (before) | `/smart-routine` | Plain activity list, no timeline |
| `smart-routine-1440.png` (after) | `/smart-routine` | Visual timeline rail, conflict warnings, timezone note |
| `impact-1440.png` (before) | `/impact` | Table of entries, no KPI strip |
| `impact-1440.png` (after) | `/impact` | KPI strip + units/method card + honest accounting badge |

## 6. What was preserved (not changed)

- All 11 routes remain functional with their original `h1` headings.
- Backend API contracts unchanged: `/healthz`, `/api/v1/air-quality/current`, CORS `Access-Control-Allow-Origin: http://localhost:3000`.
- All seven modules keep their data schemas, local storage keys and core behaviour.
- Emission factors are only those served by the Impact factor registry; no fabricated factors.
- No environmental data is ever invented; unavailable data shows explicit empty states with provider reasons.
- The constrained Copilot response schema is preserved; only `source===ai` may be labelled AI.
- Test-locked strings (`Current conditions`, `Choose a location to begin`, `No CPCB index this hour`, `Retry`, `Not reported`, `Car`, `Cycling`, `1.6 kg`, `78 / 100`) remain exactly as before.
- ESLint, TypeScript, Vitest and production build are clean — no regressions introduced.

## 7. Verdict

The Step 29 transformation delivers a premium, production‑quality environmental intelligence platform without inventing data, breaking any existing route, or weakening any test. The visual language is consistent, the navigation is grouped and collapsible, the map behaves reliably, and every module has honest loading/error/empty states. The pre‑existing coverage gate (78.86 %) is documented and not suppressed. All 11 routes, 149 unit tests and 380 E2E assertions pass.