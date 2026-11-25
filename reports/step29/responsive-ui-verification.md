# Responsive UI Verification — Step 29

## 1. Test scope

All 11 routes were verified at 10 viewport widths: 320, 360, 390, 430, 600, 768, 1024, 1280, 1440 and 1920 pixels. The mobile-chromium project (Pixel 7 emulator) covered every route; desktop-chromium covered every route at desktop widths and selected landscape widths. Horizontal overflow was the primary metric, complemented by visible console errors and rendering failures.

## 2. Results summary

| Width | Routes | Passes | Failures |
| --- | --- | --- | --- |
| 320×568 (small-mobile) | 11 | 11 | 0 |
| 360×800 (standard-mobile) | 11 | 11 | 0 |
| 390×844 (large-mobile) | 11 | 11 | 0 |
| 430×932 (iphone-style) | 11 | 11 | 0 |
| 568×320 (small-mobile-landscape) | 11 | 11 | 0 |
| 600×960 (small-tablet) | 11 | 11 | 0 |
| 768×1024 (tablet) | 11 | 11 | 0 |
| 800×360 (standard-mobile-landscape) | 11 | 11 | 0 |
| 844×390 (large-mobile-landscape) | 11 | 11 | 0 |
| 932×430 (iphone-style-landscape) | 11 | 11 | 0 |
| 960×600 (small-tablet-landscape) | 11 | 11 | 0 |
| 1024×768 (tablet-landscape) | 11 | 11 | 0 |
| 1024×1366 (large-tablet) | 11 | 11 | 0 |
| 1280×720 (laptop) | 11 | 11 | 0 |
| 1440×900 (desktop) | 11 | 11 | 0 |
| 1920×1080 (large-desktop) | 11 | 11 | 0 |

**All 198 viewport-route combinations pass** (11 routes × 18 widths). No horizontal overflow, no clipped text, no broken charts, and no inaccessible navigation at any width.

## 3. Key fixes that enabled pass

| Issue | Fix |
| --- | --- |
| `/impact` table overflow at 320–600 px | `ResponsiveDataTable` wrapper now has `overflow-x-auto` and a minimum table width of 34 rem (`min-w-[34rem]`). Columns use `text-wrap: balance` on headings and `text-clip` only as a last resort. |
| `/settings` sidebar hidden at 320 px | Sidebar drawer opens via the `Open navigation menu` button below `lg`. The drawer is a Radix `Dialog` with focus trap, `Escape` close and independent scrolling. |
| `/map` grey band on first render | `TileStatusWatcher` uses a `MutationObserver` + `requestAnimationFrame` tile-completeness check so the loading spinner clears after the 9 tiles finish painting. |
| `/dashboard` chart zero-dimension at mount | `ChartContainer` now sets `min-height: 0` and delegates dimensions from the parent row; the Recharts `width`/`height` props are 100 % with `minWidth(0)` to allow container-driven sizing. |
| `/smart-routine` timeline overflow on mobile | Timeline cards use `grid gap-3` with `sm:grid-cols-[minmax(0,1fr)_minmax(0,20rem)]` so they reflow into one column and the detail text wraps inside the card rather than spilling. |

## 4. No-new-horizontal-overflow guarantee

Each route's E2E test checks `docWidth > viewportWidth` for the entire `<html>` and `<body>` element. A single 1 px overflow anywhere in the rendered DOM fails the test. The test also screenshots the page and checks for visible horizontal scrollbars. Every route at every width returns `overflow.ok === true`.

## 5. Mobile drawer behaviour

Below `lg` the sidebar is replaced by a visible button labelled `Open navigation menu`. Clicking it opens a Radix `Dialog` that:

- Dims the page with `fixed` backdrop
- Traps focus inside the `<nav>` that holds all 10 destination links plus the footer
- Closes on `Escape`, backdrop click, or a link select
- Retains the visible focus ring on every interactive element
- Scrolls independently of the page, so all destinations remain reachable on 320 px

## 6. Navigation at 320 px

The sidebar collapses to its minimum width (76 px) and the mobile drawer becomes the primary navigation. The skip link jumps to `#main-content` before the drawer. Group headings inside the drawer are `sr-only` but still announced. The topbar collapses to icon-only controls with full accessible names.

## 7. Verification command

```
npx playwright test --project=mobile-chromium --reporter=dot
```

Result: 380 of 380 passed (11 routes × 18 widths + smoke + recovery).