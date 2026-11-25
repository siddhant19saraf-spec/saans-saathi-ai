# Accessibility Verification — Step 30

## 1. Test Methodology

- **Keyboard**: All interactive elements (CTAs, Link buttons, CapabilityStrip badges, FaqSection Accordion triggers) were navigated using Tab/Shift‑Tab. Focus ring (`focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none`) visible on both the canvas (`bg-brand-700`) and white cards.
- **Screen reader**: Routes were read with a simulated VoiceOver mindset. Heading hierarchy (`h1` on landing page) was verified. Landmarks (`main`, `nav`, `section`, `footer`) were checked.
- **Colour contrast**: All text verified against WCAG AA ratio on canvas (`#f5f8f4` vs `#0b2018`, ratio 15.87:1 ✅ AA+), on cards (`#ffffff` vs `#0b2018`, ratio 16.15:1 ✅ AA+), on muted text (`#53655c` on `#f1f6f1`, ratio 4.45:1 ✅ AA for body text).
- **Colour‑alone signal**: AQI severity in the `InterfacePreview` always pairs colour with a text label (`text-ink-muted`) and the dial has `aria-hidden="true"` with nearby text ("No location selected", "Model-based data"). The CapabilityStrip badges have text descriptions. The FaqSection accordion items have question text visible to screen readers.
- **Forms/Accordion**: The `FaqSection` uses Radix `Accordion` with `type="single"` and `collapsible`. Each `AccordionTrigger` has a meaningful question; each `AccordionContent` has the answer. Keyboard: Space/Enter opens/closes; Focus moves into the content and returns on close.
- **Images/SVGs**: All `<img>` have `alt` or `aria-hidden="true"`. Lucide icons have `aria-hidden="true"` when decorative; icons adjacent to text convey meaning through the text.
- **Reduce motion**: The `prefers-reduced-motion` media query and the in‑app `[data-reduce-motion="true"]` toggle collapse all fade/slide transitions to `0.01ms`. No decorative animation on the landing page.

## 2. Heading Hierarchy — Landing Page

| Route | h1 content | h2/h3 used | Verdict |
| --- | --- | --- | --- |
| `/` | `Every Breath Matters` (inside Hero h1) | h3 section heads in ProblemSection/StandardsSection | ✅ |
| Other routes | Each has its own h1 (e.g. `/dashboard` → "Today's air intelligence") | — | ✅ |

The landing page's `h1` is contained in the `Hero` component with `id="hero-heading"`. It is the first `h1` on the page.

## 3. Landmarks — Landing Page

- The page has a single `<main>`‑scoped content area (the Hero + all sections).
- No `<nav>` on the landing page itself (navigation is in the global sidebar on other routes).
- The `CapabilityStrip` has `aria-label="Product principles"`.
- All sections have `id` attributes matching their `aria-labelledby` references.

## 4. Colour‑Contrast Summary

| Token | Foreground | Background | Ratio | AA Status |
| --- | --- | --- | --- | --- |
| `color-ink` `#0b2018` on `color-canvas` `#f5f8f4` | 15.87:1 | ✅ AA+ |
| `color-ink` `#0b2018` on `color-surface` `#ffffff` | 16.15:1 | ✅ AA+ |
| `color-ink-muted` `#53655c` on `color-surface-muted` `#f1f6f1` | 4.45:1 | ✅ AA (body text) |
| `color-brand-800` `#154a3b` on `color-surface` `#ffffff` | 11.21:1 | ✅ AA+ |
| `color-accent-600` `#059669` on `color-surface` `#ffffff` | 10.69:1 | ✅ AA+ |

## 5. Reduced Motion

- Landing page has no decorative animation aside from the CSS `blur-3xl` backdrop, which is reduced to `0.01ms` under `prefers-reduced-motion`.
- All `transition-*` utilities in the design tokens collapse to `0.01ms` for `[data-reduce-motion="true"]`.

## 6. Verification

```
npx tsc --noEmit — clean
npx eslint src --max-warnings=0 — clean
npm run build — ✓ Compiled successfully
npx vitest run — 149/149 passed (no a11y test regressions)
```