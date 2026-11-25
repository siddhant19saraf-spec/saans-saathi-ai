# Navigation Improvements — Step 30

## 1. Current State

The landing page's top-level navigation is embedded in the `Hero` component and the global sidebar. The Hero contains two CTAs ("Open dashboard" and "Explore air intelligence") that link to `/dashboard` and `/air-quality` respectively. The global sidebar (outside the landing page, active on all routes) contains 9 navigation items (including Settings) grouped into 5 named groups:

- `Workspace`: Dashboard, Air intelligence, Pollution map
- `Personal protection`: Family intelligence, SmartRoutine, IndoorShield
- `Sustainability`: EcoRoute, Impact intelligence
- `Assistance`: SAANS AI Copilot
- `Preferences`: Settings

The `CapabilityStrip` below the Hero reinforces four product principles as badge items.

## 2. Navigation Links from Landing Page

| CTA | Destination | Route | Status |
| --- | --- | --- | --- |
| "Open dashboard" | Dashboard route | `/dashboard` | ✅ Working |
| "Explore air intelligence" | Air intelligence route | `/air-quality` | ✅ Working |

Both CTAs use `Link` components with `asChild` + `Button`, consistent with the UI pattern.

## 3. Sidebar Navigation (active on all routes)

The sidebar is the primary navigation mechanism. It displays 9 destination links organized by group. Below `lg` breakpoint, the sidebar collapses to an icon-only mode (76 px) with a collapse/expand button. Below `lg`, a mobile drawer (Radix `Dialog`) slides from the left and contains all 9 links plus a footer with the "Every Breath Matters" tagline.

### Group labels (visible in expanded sidebar)

- `Workspace` (3 items)
- `Personal protection` (3 items)
- `Sustainability` (2 items)
- `Assistance` (1 item: Copilot)
- `Preferences` (1 item: Settings)

### Mobile drawer

- Opened by the `Open navigation menu` button (visible below `lg`).
- Focus‑trapped Radix `Dialog` with `DialogTitle` "Navigation".
- All 9 links are keyboard navigable (Tab/Shift‑Tab) and announced.
- `Escape` closes the drawer; selecting a link also closes it.
- Focus ring (`focus-visible:ring-2 focus-visible:ring-brand-600`) visible on every link.

## 4. CapabilityStrip Navigation Role

The `CapabilityStrip` does not navigate anywhere; it is an informational bar with four badge items:

1. No fabricated readings
2. Source‑aware states
3. Location you control
4. Accessible by default

Each badge has an icon and a short description. Clicking a badge does nothing — it is purely educational.

## 5. Verification

```
npx tsc --noEmit — clean
npx eslint src --max-warnings=0 — clean
npm run build — ✓ Compiled successfully
npx vitest run — 149/149 passed (no regression)
```