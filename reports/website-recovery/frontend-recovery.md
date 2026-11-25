# Frontend Recovery — SAANS SAATHI AI Website

**Status:** COMPLETE — frontend verified working; no application code change required  
**Date:** Mon Nov 23 2026  
**Engineer:** Principal Full-Stack / Next.js

## Finding

The frontend was **not broken**. Direct browser forensics on the production build (`npm run start`, Next.js 16.4.6 Turbopack, React 19.3.1) showed:

- All 11 routes return HTTP 200 with complete SSR HTML (sidebar, footer, "Today's air intelligence" present in raw HTML).
- React fully hydrates every route: `#S:0` streaming shell revealed, root `loading.tsx` fallback removed, `#main-content`/`<nav>` claimed (238 React-owned elements), all 11 nav links present, `h1` visible.
- **Zero** console errors or warnings on every route.
- Client-side navigation between modules works (URL changes, new `h1` renders).
- Real API data flows: `/api/v1/air-quality/current?lat=28.61&lon=77.21` → 200, `cpcb_aqi` 264 ("poor").

The "stuck loading" appearance was an **eager-inspection artifact**: probes ran before `requestAnimationFrame` fired React's `$RT`/`$RV`/`$RB` reveal machinery (see `root-cause-analysis.md`). Re-probing the same tab after rAF fired showed full hydration. Playwright's auto-retrying assertions confirm: **13/13 E2E tests passed**.

## Frontend code state (verified, not rebuilt)

| Component | File | Status |
|---|---|---|
| Root layout | `src/app/layout.tsx` | OK — imports Inter font, metadata, viewport |
| Root loading | `src/app/loading.tsx` | OK — SSR fallback, correctly removed after hydration |
| Root error | `src/app/error.tsx` | OK — route error boundary |
| App (shell) layout | `src/app/(app)/layout.tsx` | OK — wraps `AppShell` |
| App shell | `src/components/layout/app-shell.tsx` | OK — `<main id="main-content">` + `LocationProvider` |
| Sidebar nav | `src/components/navigation/sidebar-nav.tsx` + `nav-config.ts` | OK — 7 modules + settings |
| Marketing page | `src/app/(marketing)/page.tsx` | OK — h1 "Every Breath Matters." |

## Module view components (all present, all hydrate verified)

| Module | Route | h1 (SSR) | Loading skeleton | Hydrated (E2E) |
|---|---|---|---|---|
| Dashboard | `/dashboard` | Today’s air intelligence | Loading your workspace | ✅ |
| Air intelligence | `/air-quality` | Air quality in detail | Loading air intelligence | ✅ |
| Family intelligence | `/family` | Family intelligence | Loading family intelligence | ✅ |
| SmartRoutine | `/smart-routine` | SmartRoutine | Loading routine planner | ✅ |
| IndoorShield | `/indoor-shield` | IndoorShield | Loading indoor checklist | ✅ |
| EcoRoute | `/eco-route` | EcoRoute | Loading route preferences | ✅ |
| Impact intelligence | `/impact` | Impact | Loading activity log | ✅ |
| SAANS AI Copilot | `/copilot` | SAANS AI Copilot | (none — loads on send) | ✅ |
| Pollution map | `/map` | Choose a place on the map | Loading the map | ✅ |
| Settings | `/settings` | Settings | Loading settings | ✅ |
| Marketing | `/` | Every Breath Matters. Every Decision Counts. | Loading content | ✅ |

## Storage / hydration hooks (prime suspect — cleared)

`src/features/store/storage.ts` `useHydrated()`:
```ts
export function useHydrated(): boolean {
  return useSyncExternalStore(
    emptySubscribe,
    () => true,   // client snapshot
    () => false,  // server snapshot
  );
}
```
- Uses `useSyncExternalStore` with identical server/client snapshots — correct hydration hygiene.
- Not the cause of any stall. `useStoredState()` gates `localStorage` reads behind `hydrated`, keeping SSR/client markup identical.
- `localStorage` empty (0 keys) is expected for a fresh session — `LocationGate` does not block rendering; `hydrated` flips to `true` after client mount.

## Environment

`frontend/.env.local`:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```
`frontend/src/lib/env.ts` validates `NEXT_PUBLIC_API_BASE_URL` via `z.url({ protocol: /^https?$/ }).default("http://localhost:8000")` — accepts both `http://` and `https://`; `undefined` falls back to localhost:8000. Verified with Zod directly. Not a defect.

`frontend/next.config.ts`: security headers only (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Cross-Origin-Opener-Policy`, `Permissions-Policy`), `reactStrictMode: true`, `turbopack.root` set. No CSP — inline scripts allowed. Correct.

## Verification results

| Suite | Result |
|---|---|
| `npm run build` | PASS — 11 static routes + `_not-found` |
| Vitest | 149 passed / 28 files (14.49s) |
| ESLint | clean (exit 0) |
| `tsc --noEmit` | clean (exit 0) |
| Playwright E2E | 13/13 passed — all routes hydrate, zero console/page errors |

## Conclusion

Frontend recovery is complete. No application code was changed (none required). All seven modules plus shell routes render real content after hydration, client-side navigation works, and API calls fire correctly. The deployment config fix (`vercel.json`: `next.config.js` → `next.config.ts`) ensures Vercel builds against the real config file.
