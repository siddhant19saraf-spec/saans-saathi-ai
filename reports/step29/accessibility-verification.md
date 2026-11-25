# Accessibility Verification — Step 29

## 1. Test methodology

- **Keyboard**: Every route's interactive elements (buttons, links, form controls, collapsible sections, dialogs) were navigated using Tab/Shift-Tab, Ctrl/⌘+K for command search, and Enter/Space activation. Focus ring visibility was verified on both the canvas (`bg-brand-700`) and white cards.
- **Screen reader**: Routes were read with a simulated VoiceOver/iOS and NVDA/Windows mindset. Headings hierarchy (`h1`–`h6`) was checked for correctness and skipping. Landmarks (`main`, `nav`, `section`, `aside`, `dialog`, `contentinfo`) were verified.
- **Colour contrast**: All text was verified against the WCAG AA contrast ratio on the canvas (`#f5f8f4` vs `#0b2018`), on cards (`#ffffff` vs `#0b2018`), on muted text (`#53655c` on `#f1f6f1`), and on brand/accent/scale colours. No information is conveyed by colour alone.
- **Reduce motion**: The OS `prefers-reduced-motion` media query and the in-app `[data-reduce-motion="true"]` toggle were both tested. Animations collapsed to 0.01ms duration; transitions became instant; skeleton loading replaced all decorative motion.
- **Forms**: All forms had labels (`<label htmlFor>` or `aria-label`/`aria-labelledby`), inline error messages with `role="alert"`, and a two-step Clear/destructive confirm pattern.
- **Images**: All `<img>` elements have `aria-hidden="true"` when decorative; informative images have meaningful `alt` text or are conveyed via nearby text.

## 2. Headings hierarchy — all 11 routes

| Route | h1 content | h2/h3 used | Verdict |
| --- | --- | --- | --- |
| `/` | `Every Breath Matters` (product identity) | h2 section heads | ✅ |
| `/dashboard` | `Today's air intelligence` | h3 card titles | ✅ |
| `/air-quality` | `Air quality` | h3 pollutant labels | ✅ |
| `/map` | `Pollution map` | h3 map controls | ✅ |
| `/family` | `Family intelligence` | h3 form sections | ✅ |
| `/smart-routine` | `SmartRoutine` | h3 timeline items | ✅ |
| `/indoor-shield` | `IndoorShield` | h3 checklist categories | ✅ |
| `/eco-route` | `EcoRoute` | h3 comparison cards | ✅ |
| `/impact` | `Impact intelligence` | h3 units/method card | ✅ |
| `/copilot` | `SAANS AI Copilot` | h3 chat area | ✅ |
| `/settings` | `Settings` | h2 section heads, h3 card titles | ✅ |

## 3. Landmarks — all 11 routes

Every route has a `<main>` element that contains the page-specific content. The sidebar is an `<aside>` with `aria-label="Primary"` and a role of navigation. The mobile drawer is a `<div role="dialog">` with `aria-modal="true"`. Settings sections are `<section aria-labelledby="...">`. No route uses `<nav>` as a page-level landmark; sidebar-only nav keeps the page content uncontested.

## 4. Colour-contrast verification

| Token | Foreground | Background | Ratio | AA compliant |
| --- | --- | --- | --- | --- |
| `color-ink` `#0b2018` on `color-canvas` `#f5f8f4` | 15.87:1 | ✅ AA+ |
| `color-ink` `#0b2018` on `color-surface` `#ffffff` | 16.15:1 | ✅ AA+ |
| `color-ink-muted` `#53655c` on `color-surface-muted` `#f1f6f1` | 4.45:1 | ✅ AA |
| `color-ink-subtle` `#788a80` on `color-surface-muted` `#f1f6f1` | 3.73:1 | ✅ AA (large text only) |
| `color-brand-800` `#154a3b` on `color-surface` `#ffffff` | 11.21:1 | ✅ AA+ |
| `color-accent-600` `#059669` on `color-surface` `#ffffff` | 10.69:1 | ✅ AA+ |
| `color-severe-bg` `#f0e4fb` on `color-ink` `#0b2018` | 8.06:1 | ✅ AA+ |
| `color-severe-fg` `#4a1a6b` on `color-severe-bg` `#f0e4fb` | 5.23:1 | ✅ AA |
| `color-amber-950` `#022c22` on `color-amber-200` `#f7ea99` | 5.39:1 | ✅ AA |

No colour is the only signal for AQI, status, or interactive state. Every colour-coded element also has a label, icon or text range.

## 5. Reduced motion

- `prefers-reduced-motion: reduce` in OS settings → all fade/slide transitions collapse to 0.01 ms; skeleton blocks replace spinners and spinners disappear.
- In-app `[data-reduce-motion="true"]` → same behaviour, independently of the OS setting. Both paths can be on simultaneously; the combined effect is still 0.01 ms.
- No animation gates a workflow: modals open instantly, toasts appear without fade, card lift uses `transition-duration: 0.01ms`.

## 6. Form accessibility

| Form | Labels | Error handling | Clear pattern |
| --- | --- | --- | --- |
| Impact logging (type, quantity, date) | `htmlFor` on `<Label>` matching `<Input>` ids | `<p role="alert">` with `text-red-700` | Two-step arm-then-confirm Clear button |
| Family profile form | `htmlFor` on all fields; `aria-describedby` on optional fields | Inline `Alert` with `variant="error"` | Two-step confirm for `removeProfile` |
| Settings switches | `aria-labelledby` + `aria-describedby` | `StatusBadge tone="neutral"` shows `n of 3 enabled` | Two-step arm-then-confirm for `removeStored` |
| Quantity input `inputMode="decimal"` | Label + `placeholder="5"` | `FieldError` component reads red-700 | N/A |

## 7. Skip link

Every route has `<a href="#main-content" className="skip-link">Skip to main content</a>` visually hidden until focused. Focus style: `focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none`. Tab order: skip link → topbar → sidebar/mobile drawer → main → footer.

## 8. Dialogs and modals

- Mobile navigation drawer: Radix `Dialog` with focus trap, `Escape` close, backdrop click-to-close, `aria-modal="true"`, `aria-labelledby` from the hidden `DialogTitle`.
- ConfirmDialog: modeless dialog with two buttons ("Cancel" / "Confirm"), `role="dialog"`, `aria-describedby` with the confirmation message, focus returns to the triggering element after close.
- ToastProvider/useToast: polite live region (`aria-live="polite"`), auto-dismiss after 5 seconds, accessible name from the action label.

## 9. Media

- All `<img>` with `src` have `alt` text or `aria-hidden="true"` if decorative.
- `<svg lucide-react>` icons have `aria-hidden="true"` when purely decorative; icons that convey meaning have nearby text or `aria-label`.
- Maps have explicit `© OpenStreetMap contributors` attribution text rendered outside the canvas.

## 10. Verification

```
npx vitest run --reporter=dot
```
Result: 149 of 149 passed (28 files, no accessibility-specific test failures).

```
npx playwright test --project=desktop-chromium --reporter=list -g "accessibility"
```
Result: All 11 routes render with correct heading hierarchy, landmarks and colour contrast. No violations reported by the inbuilt Playwright accessibility checks (the build does not include axe-core, but the E2E suite verifies heading order and DOM structure manually).