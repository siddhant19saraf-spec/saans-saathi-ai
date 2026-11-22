# SAANS SAATHI AI — Accessibility Audit

**Audit date:** 2026-11-21  
**Scope:** Keyboard navigation, ARIA labels, focus management, color contrast, skip links, landmarks, form validation

---

## Keyboard Navigation

| Feature | Implementation | Status |
|---------|---------------|--------|
| Skip link | `SkipLink` component renders first, links to `#main-content` | ✓ |
| Tab order | Logical DOM order; SkipLink → Logo → Topbar → Main content | ✓ |
| Keyboard shortcuts | `CommandSearch` opens on `Cmd/Ctrl + K` | ✓ |
| Dialog Escape | Dialogs close on Escape key | ✓ |
| Focus management | `inputRef` for CommandSearch; `scrollIntoView` stubbed in tests | ✓ |
| No focus traps broken | Radix UI dialogs manage focus correctly | ✓ |

## ARIA & Landmarks

| Feature | Implementation | Status |
|---------|---------------|--------|
| Main landmark | `<main id="main-content">` in `AppShell` | ✓ |
| Navigation landmarks | `aria-label="Primary"` topbar, `aria-label="Breadcrumb"` breadcrumbs, `aria-label="Site"` marketing nav | ✓ |
| Region labels | `aria-labelledby` on dashboard sections (insights, current conditions, etc.) | ✓ |
| Button labels | All buttons have visible text or `aria-label` (Search pages, Add coordinates, Use my location, etc.) | ✓ |
| Link labels | Descriptive link text (Open dashboard, Manage notification preferences, Back to home) | ✓ |
| Image alt | Icons use `aria-hidden="true"`; meaningful images have alt text | ✓ |
| Live regions | `aria-live="polite"` on loading skeletons; `aria-busy` on async content | ✓ |

## Forms & Validation

| Feature | Implementation | Status |
|---------|---------------|--------|
| Form labels | All inputs have associated `<Label>` or `aria-label` | ✓ |
| Field errors | `FieldError` component with `aria-invalid` on invalid fields | ✓ |
| Required indicators | Schema-level `min`/`max` validation with user-facing messages | ✓ |
| Consent gating | Health-flag consent checkbox with descriptive label | ✓ |
| Error association | Errors linked to fields via `aria-describedby` patterns | ✓ |

## Color & Contrast

| Feature | Implementation | Status |
|---------|---------------|--------|
| Badge variants | `neutral`, `warning`, `destructive`, `outline` variants with semantic colors | ✓ |
| Severity badges | CPCB AQI severity color-coded (good/satisfactory/moderate/poor/very_poor/severe) | ✓ |
| Focus rings | `focus-visible:ring-2 focus-visible:ring-brand-600` on interactive elements | ✓ |
| Disabled states | `data-[disabled]:opacity-50`, `pointer-events-none` | ✓ |

## Motion & Reduced Motion

| Feature | Implementation | Status |
|---------|---------------|--------|
| No autoplay | No auto-playing media or animations | ✓ |
| Loading skeletons | Static skeletons (no pulsing animation) | ✓ |

## Screen Reader Considerations

| Feature | Implementation | Status |
|---------|---------------|--------|
| SR-only text | `sr-only` class for visually hidden labels (e.g., "Loading the map") | ✓ |
| `aria-hidden` | Decorative icons hidden from screen readers | ✓ |
| `aria-live` | Polite updates for dynamic content | ✓ |
| Dialog roles | Radix `Dialog` with `DialogTitle`, `DialogDescription` | ✓ |
| Menu roles | `role="menu"`, `role="menuitem"` on user menu and notifications | ✓ |

## Gaps / Limitations

| Area | Detail |
|------|--------|
| No automated a11y testing | axe-core / @axe-core/react not integrated into test suite |
| No color contrast audit | Contrast ratios not programmatically verified |
| No screen reader testing | Not tested with NVDA/JAWS/VoiceOver |
| No keyboard-only testing | Not tested end-to-end with keyboard only |
| No reduced-motion preference | `prefers-reduced-motion` media query not checked |
