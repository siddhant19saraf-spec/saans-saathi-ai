# Cross-Browser Compatibility Report — SAANS SAATHI AI

**Status:** PARTIAL — Chromium tested; others NOT TESTED  
**Date:** Mon Nov 23 2026  
**Engineer:** Principal Full-Stack / Frontend

## Browser test results

| Browser | Engine | Status | Details |
|---|---|---|---|
| Google Chrome | Chromium | PASS | Tested via Playwright desktop-chromium at all 16 viewport sizes |
| Microsoft Edge | Chromium | NOT TESTED | Same engine as Chrome but not independently verified |
| Mozilla Firefox | Gecko | NOT TESTED | Not available in test environment |
| Safari/WebKit | WebKit | NOT TESTED | Not available on this platform |

## Chromium (Chrome) test details

**Test environment:** Playwright `desktop-chromium` against dev server at `http://localhost:3000`

**Tests run:** 175 E2E tests
- 110 tests: All 11 routes at 10 portrait viewports (320×568 through 1920×1080)
- 54 tests: 9 routes at 6 landscape viewports
- 10 tests: All 7 modules at 320×568 (small mobile)
- 1 test: Mobile hamburger navigation

**Result:** 175 passed, 0 failed

**Checks performed per test:**
- HTTP 200 status
- Route hydration (shell revealed, loading fallback removed, React >50 elements, h1 visible)
- Exact `<h1>` visible inside `<main>`
- No horizontal overflow (`documentWidth <= viewportWidth`)
- Zero console errors
- Zero uncaught page errors

## Edge (Chromium)

**Status:** NOT TESTED

Edge shares the Chromium engine with Chrome, so results are expected to be similar. However, per the requirement "Do not claim a browser is verified unless actually tested," Edge is marked NOT TESTED.

To test Edge: install Playwright Chromium with Edge channel and run `npx playwright test e2e/responsive.spec.ts --project=desktop-chromium --browser=chromium:channel=msedge`.

## Firefox (Gecko)

**Status:** NOT TESTED

Firefox uses the Gecko engine, which has different CSS layout behavior (particularly for CSS Grid subgrid, `gap`, and form styling). Potential areas of difference:
- CSS Grid `minmax()` behavior in form layouts
- `-webkit-backdrop-filter` support (used in topbar)
- Form input styling (especially `input[type=date]`, `input[type=time]`)
- Focus ring rendering

To test Firefox: install Playwright Firefox and run `npx playwright test e2e/responsive.spec.ts --project=desktop-firefox`.

## Safari/WebKit

**Status:** NOT TESTED

Safari uses WebKit, which has different behavior for:
- `backdrop-blur` (used in topbar header)
- CSS `dvh` (dynamic viewport height) support on iOS Safari
- `-webkit-overflow-scrolling` for momentum scrolling
- Form field styling on iOS
- `viewport-fit=cover` and safe area insets for notch devices

To test Safari: install Playwright WebKit and run `npx playwright test e2e/responsive.spec.ts --project=desktop-webkit`.

## CSS features used and browser support

| Feature | Chrome | Edge | Firefox | Safari | Fallback |
|---|---|---|---|---|---|
| CSS Grid | ✅ | ✅ | ✅ | ✅ | Flex stack |
| CSS Flexbox | ✅ | ✅ | ✅ | ✅ | Block flow |
| `backdrop-filter` | ✅ | ✅ | ✅ | ✅ | Solid bg |
| `dvh` units | ✅ | ✅ | ✅ | Partial (iOS) | `vh` fallback |
| `focus-visible` | ✅ | ✅ | ✅ | ✅ | Always focus ring |
| `input[type=date]` | ✅ | ✅ | ✅ | ✅ | Text input |
| `input[type=time]` | ✅ | ✅ | ✅ | ✅ | Text input |

## JavaScript compatibility

- React 19.3.1 — supports all modern browsers
- Next.js 16.4.6 — supports all modern browsers
- `AbortController` — supported in all target browsers
- `crypto.randomUUID()` — supported in all target browsers (with fallback in copilot-view.tsx)
- `ResponsiveObserver` (Recharts) — supported in all target browsers
- `localStorage` — supported in all target browsers

## Recommendations

1. **Test Edge:** Install Playwright with MS Edge channel and run the responsive E2E suite.
2. **Test Firefox:** Install Playwright Firefox and verify CSS Grid layouts render correctly.
3. **Test Safari/WebKit:** Install Playwright WebKit and verify `backdrop-filter`, `dvh`, and iOS safe-area behavior.
4. **Test on physical devices:** Emulator testing does not substitute for real device testing, particularly for touch targets and safe areas on iPhones with dynamic island/notch.

## Conclusion

Cross-browser compatibility: **PARTIAL**. Chromium (Chrome) fully tested and passing (175/175 tests). Edge, Firefox, and Safari are NOT TESTED and should be verified before production release.
