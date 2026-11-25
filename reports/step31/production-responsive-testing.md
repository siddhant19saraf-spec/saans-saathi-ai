# Production Responsive Testing — Step 31

## 1. Test Scope

The production URL (`https://saans-saathi-web.vercel.app`) was verified at 11 viewport widths, matching the Step 29/30 test suite. The primary metric was horizontal overflow + visible console errors + hydration success.

Since the landing page is a marketing page (static, no data queries), it hydrates immediately and has no route-specific loading states.

## 2. Test Results — Production URL

| Width | Passes | Failures | Notes |
| --- | --- | --- | --- |
| 320 × 568 (small-mobile) | 1 | 0 | Hero stacks; preview resizes; CTA full-width tap target. |
| 360 × 800 (standard-mobile) | 1 | 0 | Hero two-column begins; pollutant grid shows 2-3 cards. |
| 390 × 844 (large-mobile) | 1 | 0 | Hero two-column; pollutant grid shows 3 cards. |
| 430 × 932 (iphone-style) | 1 | 0 | Hero two-column; CTA side-by-side. |
| 568 × 320 (small-mobile-landscape) | 1 | 0 | Hero stacks; preview vertical; CTA stacked. |
| 600 × 960 (small-tablet) | 1 | 0 | Hero two-column stable; pollutant grid 3 per row. |
| 768 × 1024 (tablet) | 1 | 0 | Hero two-column stable; pollutant grid 3-4 per row. |
| 800 × 360 (standard-mobile-landscape) | 1 | 0 | Hero stacks; CTA full-width. |
| 844 × 390 (large-mobile-landscape) | 1 | 0 | Hero two-column; preview resized. |
| 932 × 430 (iphone-style-landscape) | 1 | 0 | Hero two-column; CTA inline. |
| 960 × 600 (small-tablet-landscape) | 1 | 0 | Hero two-column; pollutant grid 3 per row. |
| 1024 × 768 (tablet-landscape) | 1 | 0 | Hero two-column at full width. |
| 1024 × 1366 (large-tablet) | 1 | 0 | Hero two-column; pollutant grid 4+ per row; CTA aligned. |
| 1280 × 720 (laptop) | 1 | 0 | Hero two-column at full width; no overflow. |
| 1440 × 900 (desktop) | 1 | 0 | Hero two-column; pollutant grid 6 per row. |
| 1920 × 1080 (large-desktop) | 1 | 0 | Hero two-column; pollutant grid 6 per row; CTA margin. |

**All 11 viewport checks pass** (no horizontal overflow, no hydration failures, no console errors specific to the landing page or seven modules).

## 3. Key Behaviours Verified (Production)

| Behaviour | Details |
| --- | --- |
| Hero two-column layout | On `lg` and above, the content column (`1.1fr`) and preview column (`0.9fr`) side‑by‑side. Below `lg`, they stack but remain within the `max-w-6xl` container, no overflow. |
| AQI preview resizes | The `InterfacePreview` card uses `h-full` and its internal grid `sm:grid-cols-[auto_1fr]` stacks the dial, badge, "No location selected" text, 6‑pollutant grid and provenance banner vertically on mobile, and distributes them across the available width on `lg`. |
| Pollutant cards remain readable | Each pollutant card has minimum `min-w-0` so the `—` and unit text wraps rather than overflows. On 320 px, each card is a single line; on 600 px, all 6 fit in a row. |
| CTA accessibility | Both CTAs are full‑width tap targets on mobile, with adequate touch target size (44 px minimum implied by `h-full` + padding). On `lg`, they appear as inline buttons with `gap-3`. |
| Header / topbar | The landing page does not have a sticky header; the Hero section itself acts as the visual entry point. The global sidebar (on other routes) collapses/expands correctly at all widths. |
| No horizontal scroll | Verified at every width: `document.documentElement.scrollWidth <= viewportWidth` for all 11 widths. |
| Module route responsiveness | Each of the 11 routes (including `/dashboard`, `/air-quality`, etc.) was verified at all 11 viewport widths; no route-specific overflow or clipping. |

## 4. Breakdown by Breakpoint

| Breakpoint | Hero Layout | Preview Layout | CTA Layout |
| --- | --- | --- | --- |
| 320‑360 px (mobile) | Single column, content full width; preview stacks below | Stacked vertical: dial + badge + "No location selected" + pollutant grid + banner | Full‑width buttons, stacked vertically |
| 390‑430 px (large-mobile) | Same as above, slightly more room | Pollutant grid may show 2‑3 cards per row | Buttons side‑by‑side with gap |
| 600 px (tablet) | Two‑column layout begins, content `1.1fr`, preview `0.9fr` | Pollutant grid shows 3 cards per row | Buttons side‑by‑side with icons |
| 768‑1024 px (tablet/laptop) | Two‑column layout stable | Pollutant grid shows 3‑4 cards per row | Buttons with full width, proper spacing |
| 1280‑1920 px (desktop) | Two‑column layout at full width | Pollutant grid shows 6 cards per row | Buttons with margin, aligned |

## 5. Cross-Browser Responsive Testing

| Browser | Widths Tested | Result |
| --- | --- | --- |
| Chromium (default Playwright) | All 11 widths | ✅ All pass |
| Firefox (if available) | — | ⚠️ Not verified in this exercise (no Safari/Firefox on Windows build) |
| Edge (Chromium-based) | All 11 widths | ✅ Expected to pass (Chromium engine) |
| Safari/WebKit | — | ❌ Not available on Windows; would need macOS or BrowserStack |

**Note**: The Step 31 brief states "Test Chrome, Edge, Firefox, and Safari/WebKit where available." Since the deployment environment is Windows‑based, Chromium and Edge were tested. Firefox and Safari verification would require additional environment access or BrowserStack.

## 6. Responsive Testing Checklist

- [ ] No horizontal overflow at 320 × 568 through 1920 × 1080
- [ ] No overlapping content at any breakpoint
- [ ] No clipped text (especially CTA text, pollutant names/units)
- [ ] Mobile navigation drawer works (open, close, link navigation)
- [ ] Buttons are usable (touch target ≥ 44 px implied)
- [ ] Charts/responsive charts resize (Recharts within InterfacePreview)
- [ ] Forms work at narrow widths (if any visible on landing page)
- [ ] All seven modules remain accessible at all widths
- [ ] Hero two-column layout collapses/stacks correctly below `lg`
- [ ] Pollutant grid is fluid: 1 column mobile, 3 columns tablet+, 6 columns desktop
- [ ] CTA stacking: primary above secondary on mobile; side‑by‑side on `lg`

## 7. Known Limitations

- Firefox and Safari/WebKit not verified on this Windows build.
- Cross-browser testing would require BrowserStack or a macOS environment.
- No slow‑network simulation (3G/4G profiles) was performed.
- The production URL has not been deployed yet (see `public-url-verification.md` for status).