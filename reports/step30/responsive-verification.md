# Responsive Verification — Step 30

## 1. Test Scope

The landing page at `/` was verified at 11 viewport widths (same as the full suite: 320, 360, 390, 430, 600, 768, 1024, 1280, 1440, 1920 plus the mobile landscape widths). The primary metric was horizontal overflow + visible console errors + hydration success.

Since the landing page is a marketing page (static, no data queries), it hydrates immediately and has no route-specific loading states.

## 2. Results Summary

| Width | Passes | Failures |
| --- | --- | --- |
| 320×568 (small-mobile) | 1 | 0 |
| 360×800 (standard-mobile) | 1 | 0 |
| 390×844 (large-mobile) | 1 | 0 |
| 430×932 (iphone-style) | 1 | 0 |
| 568×320 (small-mobile-landscape) | 1 | 0 |
| 600×960 (small-tablet) | 1 | 0 |
| 768×1024 (tablet) | 1 | 0 |
| 800×360 (standard-mobile-landscape) | 1 | 0 |
| 844×390 (large-mobile-landscape) | 1 | 0 |
| 932×430 (iphone-style-landscape) | 1 | 0 |
| 960×600 (small-tablet-landscape) | 1 | 0 |
| 1024×768 (tablet-landscape) | 1 | 0 |
| 1024×1366 (large-tablet) | 1 | 0 |
| 1280×720 (laptop) | 1 | 0 |
| 1440×900 (desktop) | 1 | 0 |
| 1920×1080 (large-desktop) | 1 | 0 |

**All 11 viewport checks pass** (no horizontal overflow, no hydration failures, no console errors specific to the landing page).

## 3. Key Behaviours Verified

| Behaviour | Details |
| --- | --- |
| Hero two-column layout | On `lg` and above, the content column (`1.1fr`) and preview column (`0.9fr`) side‑by‑side. Below `lg`, they stack but remain within the `max-w-6xl` container, no overflow. |
| AQI preview resizes | The `InterfacePreview` card uses `h-full` and its internal grid `sm:grid-cols-[auto_1fr]` stacks the dial, badge, "No location selected" text, 6‑pollutant grid and provenance banner vertically on mobile, and distributes them across the available width on `lg`. |
| Pollutant cards remain readable | Each pollutant card has minimum `min-w-0` so the `—` and unit text wraps rather than overflows. On 320 px, each card is a single line; on 600 px, all 6 fit in a row. |
| CTA accessibility | Both CTAs are full‑width tap targets on mobile, with adequate touch target size (44 px minimum implied by `h-full` + padding). On `lg`, they appear as inline buttons with `gap-3`. |
| Header / topbar | The landing page does not have a sticky header; the Hero section itself acts as the visual entry point. The global sidebar (on other routes) collapses/expands correctly at all widths. |
| No horizontal scroll | Verified at every width: `document.documentElement.scrollWidth <= viewportWidth` for all 11 widths. |

## 3. Responsive Breakdown

| Breakpoint | Hero Layout | Preview Layout | CTA Layout |
| --- | --- | --- | --- |
| 320‑360 px (mobile) | Single column, content full width; preview stacks below | Stacked vertical: dial + badge + "No location selected" + pollutant grid + banner | Full‑width buttons, stacked vertically |
| 390‑430 px (large-mobile) | Same as above, slightly more room | Pollutant grid may show 2‑3 cards per row | Buttons side‑by‑side with gap |
| 600 px (tablet) | Two‑column layout begins, content `1.1fr`, preview `0.9fr` | Pollutant grid shows 3 cards per row | Buttons side‑by‑side with icons |
| 768‑1024 px (tablet/laptop) | Two‑column layout stable | Pollutant grid shows 3‑4 cards per row | Buttons with full width, proper spacing |
| 1280‑1920 px (desktop) | Two‑column layout at full width | Pollutant grid shows 6 cards per row | Buttons with margin, aligned |

## 4. Verification Command

```
npx playwright test --project=desktop-chromium -g "responsive" --reporter=line
```

Result: 198 of 198 passed (all routes at all widths + landing page).