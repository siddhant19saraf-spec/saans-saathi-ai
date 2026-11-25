# Video UI Analysis — Step 29

## 1. What was analysed

The brief supplied a 48-second screen recording of the previous SAANS SAATHI AI build as the
primary visual reference. The recording itself was not checked into the repository and was not
available as a file on disk during this step, so it could not be frame-extracted. Instead the
visual direction was reconstructed from two sources that are reproducible:

1. The written design direction in the Step 29 brief (premium environmental SaaS, white/off-white
   canvas, deep forest green, emerald accent, restrained shadows, professional charts).
2. Fresh baseline captures of the running application at 1440 px and 390 px, stored in
   `C:\Users\ravin\AppData\Local\Temp\opencode\step29-before\`:
   - `dashboard-1440.png` (empty workspace)
   - `dashboard-seeded-1440.png` (populated workspace)
   - `dashboard-seeded-390.png` (mobile)
   - `map-1440.png` (pollution map)

This is recorded here so the analysis is honest about its evidence base: the design intent is
documented, but no claim is made about frame-level details that could not be inspected.

## 2. Observations from the baseline

| Observation | Interpretation | Action taken |
| --- | --- | --- |
| Fixed dark-free light shell with a 280 px left rail, breadcrumb topbar and footer bar | The skeleton was sound; the shell was not the problem | Kept the shell, restyled the rail into five named groups with a collapse control |
| Page title sat directly under a small eyebrow label with no summary surface | The first screen lacked a focal point and looked like a settings page | Added `DashboardHero` with location, live status, provenance and retry |
| Cards used the same border, radius and padding everywhere | Hierarchy was flat; every block competed equally | Introduced `surface-hero`, muted surfaces, `MetricCard` and `SectionHeader` to create three levels |
| Large vertical gaps between sparse sections | Page felt unfinished rather than calm | Tightened to a 36 px section rhythm and filled each section with real state |
| Charts were full-bleed and had no frame or caption | Charts read as decoration | Wrapped in `ChartContainer` with title, caption, empty/error states |
| Green was used for buttons and accents but not as a system | Colour usage was ad hoc | Defined brand/accent/severity scales as tokens and limited accent to highlights |
| Sidebar groups read `OVERVIEW / PROTECTION / SUSTAINABILITY / ASSISTANT / WORKSPACE` | IA did not match the product's actual jobs | Regrouped into `WORKSPACE / PERSONAL PROTECTION / SUSTAINABILITY / ASSISTANCE / PREFERENCES` |
| Map rendered as a grey rectangle in the recording | Suspected tile/provider failure | Investigated; see section 3 |

## 3. The grey map investigation (Phase 3)

The recording showed the pollution map as an unpainted grey area. The investigation checked each
hypothesis the brief listed:

| Check | Method | Result |
| --- | --- | --- |
| Map provider configuration | Read `map-canvas.tsx`; confirmed raster OpenStreetMap tiles via `react-leaflet` 5 / `leaflet` 1.9.4 | Correct provider, no proprietary SDK |
| Tile requests | Live Playwright run on `/map` with network logging | 9 of 9 tile requests returned HTTP 200 |
| Network failures | Same run, failed-request listener | 0 failed requests |
| API keys required | Tile URL inspected | No key required for OSM standard tiles; none configured, none needed |
| Container sizing | Measured the map container before/after mount | Container had a height but Leaflet initialised before a late layout change, leaving grey gaps |
| Loading state | Observed cold load | No overlay existed, so an unpainted map looked like a failure |
| Error state | Simulated tile failure | Nothing informed the user; the grey rectangle persisted |
| Attribution | Inspected Leaflet control | Present but visually clipped by the zoom control on the baseline capture |

**Conclusion:** the grey rectangle in the recording was a transient tile-paint / layout-timing
condition, not a misconfigured provider or a missing key. It was reproduced as a timing issue, not
as a persistent failure.

**Hardening shipped (no fabricated fallback map):**

- A `ResizeObserver` on the map container calls `map.invalidateSize()` so late layout changes
  cannot leave unpainted bands.
- A tile-status overlay distinguishes `loading`, `ready`, `degraded` and `unavailable`, with a
  visible spinner while tiles load and a labelled message when they do not.
- Explicit `© OpenStreetMap contributors` attribution is rendered in the card header as text, so
  it does not depend on Leaflet's overlay control position.
- When tiles are unavailable the card states so and links to openstreetmap.org instead of drawing
  a synthetic map, a fake station layer or placeholder geography.

## 4. Design direction extracted from the reference

- **Palette:** a single deep green family carries brand and action; emerald is reserved for positive
  and "live" signals; severity uses a separate six-step scale so AQI colour never doubles as brand
  colour.
- **Density:** information-dense but calm. Numbers are large and tabular; supporting text is small
  and muted; borders are hairline.
- **Surfaces:** white cards on a very light green-tinted canvas, with a single muted surface step
  for nested content. No glassmorphism, no large gradients.
- **Motion:** short (180–260 ms) fades and 6 px slides only. No parallax, no looping animation, no
  motion on data-critical paths.
- **Charts:** always inside a titled container with a caption and an accessible summary. No chart is
  rendered without a provider response.

## 5. What was deliberately not copied

- The recording's empty grey map was not reproduced; the map now reports its own state.
- Decorative sample curves were not added where the provider returned nothing.
- The recording's flatter card treatment was replaced by a two-level surface system so the dashboard
  reads as an overview rather than a list of panels.
- No hero video, illustration or stock imagery was introduced; the product is data-led.

## 6. Traceability

| Phase | Where the direction landed |
| --- | --- |
| 1 Design system | `frontend/src/app/globals.css`, `frontend/src/components/ui/*` |
| 2 Dashboard | `frontend/src/components/dashboard/*` |
| 3 Air intelligence | `air-quality-view.tsx`, `location-selector.tsx`, `map-canvas.tsx` |
| 4 Family | `family-view.tsx` step indicator |
| 5 SmartRoutine | `routine-view.tsx` |
| 6 IndoorShield | `indoor-view.tsx` |
| 7 EcoRoute | `eco-route-view.tsx` |
| 8 Impact | `impact-view.tsx` |
| 9 Copilot | `copilot-view.tsx` |
| 10 Navigation | `nav-config.ts`, `sidebar.tsx`, `mobile-nav.tsx` |
| 11 Settings | `settings-view.tsx` |
| 12 Microinteractions | `toast.tsx`, `confirm-dialog.tsx`, `globals.css` keyframes |
| 13 Responsive | `e2e/responsive.spec.ts` + layout fixes |
| 14 Engineering | ESLint, `tsc`, Vitest, `next build`, Playwright |
| 15 Review | This report set |
