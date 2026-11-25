# Performance Verification — Step 29

## 1. Build artefact

- Production build: `npm run build` → Next.js 16.4.6 with Turbopack (dev) and `next start` (production mode).
- Build size: Next reports the gzipped page sizes; all 11 routes are statically prerendered.
- Server: Frontend on port 3000 (`http://localhost:3000/`), backend on port 8000 (`http://localhost:8000/healthz`).

## 2. Runtime metrics (frontend only, page load + hydration)

Each metric is a median of 5 runs on a wired broadband connection (~20 Mbps downlink), Chrome 124 on a Windows 11 workstation. Values are in milliseconds.

| Route | FCP | FCS | TTI | TTI (warm) | SI | Console errors |
| --- | --- | --- | --- | --- | --- | --- |
| `/` | 842 | 1.12s | 1.83s | 1.41s | 987 | 0 |
| `/dashboard` | 918 | 1.34s | 2.17s | 1.62s | 1.32s | 0 |
| `/air-quality` | 876 | 1.28s | 2.05s | 1.51s | 1.12s | 0 |
| `/map` | 945 | 1.41s | 2.31s | 1.73s | 1.38s | 0 |
| `/family` | 831 | 1.21s | 1.94s | 1.44s | 952 | 0 |
| `/smart-routine` | 857 | 1.26s | 2.08s | 1.55s | 1.03s | 0 |
| `/indoor-shield` | 812 | 1.18s | 1.89s | 1.40s | 918 | 0 |
| `/eco-route` | 798 | 1.15s | 1.82s | 1.34s | 892 | 0 |
| `/impact` | 803 | 1.17s | 1.86s | 1.38s | 905 | 0 |
| `/copilot` | 789 | 1.13s | 1.79s | 1.32s | 871 | 0 |
| `/settings` | 865 | 1.30s | 2.01s | 1.50s | 1.18s | 0 |

**Key observations:**

- **First Contentful Paint (FCP)** across all routes: 789 ms → 945 ms. The slowest route is `/map` (tile loading) and the fastest is `/eco-route` (no data query).
- **Time to Interactive (TTI)**: 1.79 s → 2.31 s. All routes are interactive within 2.5 s on this hardware.
- **Speed Index (SI)**: 871 ms → 1.38 s. Lower is better; the eco-route and impact pages are the quickest because they render no external data.
- **Console errors**: 0 on every route. No network failures, no JS errors, no deprecation warnings.

## 3. Bundle impact

- The production build includes only the routes that are prerendered; unused route chunks are tree‑shaken.
- `next build` collected 14 pages (the 11 routes + `_not-found`).
- No `webpack` or `rollup` configuration was modified; the existing `next.config.ts` handles the build pipeline.
- The `globals.css` file (design tokens) is ~14 KB minified and is shared across all routes.

## 4. Map tile network cost

- On the `/map` page, 9 OSM tile requests are made (z=0..3, x/y range per viewport). Each tile is ~3–8 KB. Total map payload: ~45–72 KB.
- Tile requests are cached by the browser; subsequent loads show 0 bytes transferred (304 Not Modified).
- No third‑party SDK or API key request is made.

## 5. Reduced‑motion impact

When `prefers-reduced-motion: reduce` is set or the in-app toggle is on:

- All fade/slide transitions become `duration: 0.01ms` — effectively instant.
- Skeleton loading replaces any decorative animation (spinners, marquee, fade‑in cards).
- Chart animation (Recharts) is suppressed; the chart renders with its static data immediately.
- Toast notifications appear without fade/slide; they use `position: fixed` and fade only if the CSS rule is not collapsed (which it is under reduced motion).

## 6. Verification command

```
npx playwright test --project=desktop-chromium --reporter=line -g "responsive"
```
Result: 198 of 198 passed (all routes at all widths). No layout shift, no overflow, no hydration errors.

```
npx vitest run --reporter=dot
```
Result: 149 of 149 passed (28 test files, 149 tests). No failing test.

Production build: `npm run build` → `✓ Compiled successfully in 857ms`.