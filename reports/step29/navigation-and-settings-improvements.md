# Navigation and Settings Improvements — Step 29

## Part A — Navigation

### 1. Information architecture

The sidebar previously grouped destinations as `OVERVIEW / PROTECTION / SUSTAINABILITY / ASSISTANT /
WORKSPACE`. That mixed user jobs with product areas and left Settings in a group of its own with an
unclear name. The new IA follows the brief and only contains routes that exist:

| Group | Destinations |
| --- | --- |
| **Workspace** | Dashboard (`/dashboard`), Air intelligence (`/air-quality`), Pollution map (`/map`) |
| **Personal protection** | Family intelligence (`/family`), SmartRoutine (`/smart-routine`), IndoorShield (`/indoor-shield`) |
| **Sustainability** | EcoRoute (`/eco-route`), Impact intelligence (`/impact`) |
| **Assistance** | SAANS AI Copilot (`/copilot`) |
| **Preferences** | Settings (`/settings`) |

`frontend/src/components/navigation/nav-config.ts` is the single source of truth: labels, icons,
descriptions, search keywords and the active-route matcher all come from it. `navTrail()` returns the
group name for breadcrumbs, so `/settings` now breadcrumbs as `Preferences > Settings` and
`/smart-routine` as `Personal protection > SmartRoutine`.

No destination was invented: every entry resolves to one of the 11 shipped routes.

### 2. Active state

An active item is signalled three ways at once, so it does not depend on colour:

- a 3 px brand rail on the left edge of the item,
- a tinted `brand-50` background with a `brand-100` ring,
- `aria-current="page"` for assistive technology.

Nested paths (`/smart-routine/2026-11-21`) keep the parent item active because the matcher accepts
`href` plus `/`.

### 3. Collapsible sidebar

- Expanded width 280 px, collapsed 76 px, animated only on `width` (200 ms) — no layout jank in the
  content column because the aside is a flex sibling.
- The collapse state persists in `localStorage` under `saans.v1.sidebarCollapsed`.
- Persistence uses a module-level `useSyncExternalStore` store rather than an effect, which keeps the
  render hydration-safe and satisfies the `react-hooks/set-state-in-effect` rule without a
  suppression.
- When collapsed, each item keeps its label as a native `title` tooltip, its icon stays centred, the
  label becomes `sr-only` (still announced), group headings become `sr-only`, and groups are
  separated by hairlines. The "Foundation build" card hides and a single expand button appears in the
  footer.
- Both collapse and expand buttons are real `<button>` elements with `aria-label`, `aria-expanded`
  and a visible focus ring.

### 4. Mobile drawer

- Below `lg` the sidebar is replaced by a `Menu` button labelled `Open navigation menu`.
- The drawer is a Radix `Dialog` rendered as a left sheet (`w-80`, `max-w-[85vw]`, full height), with
  a visually hidden `DialogTitle` ("Navigation") for screen readers.
- Focus is trapped inside the drawer, `Escape` closes it, the overlay is clickable, and selecting any
  destination closes it via the `onNavigate` callback.
- The drawer scrolls independently of the page, so all ten destinations plus the footer remain
  reachable on a 320 px-wide screen.

### 5. Keyboard and search

- A skip link jumps to `#main-content` before the sidebar in tab order.
- `Ctrl/⌘ + K` opens the command search from anywhere; results are keyboard navigable and route on
  Enter.
- Every interactive element uses the same focus token (`outline: 2px solid brand-700`, 2 px offset),
  so focus is visible on the canvas, on white cards and on tinted surfaces.
- Breadcrumbs remain links, not text, so a user can move up a level without the sidebar.

### 6. Topbar

The topbar keeps search, the location switcher, notifications and the workspace menu. It is sticky,
uses the same border token as the sidebar, and collapses to icon-only controls below `sm` while
retaining accessible names.

### 7. Intentional test changes

Two unit-test expectations encoded the old group names and were updated because the IA change is
deliberate:

- `nav-config.test.ts`: `navTrail("/smart-routine")?.group` — `"Protection"` → `"Personal protection"`.
- `nav-config.test.ts`: `navTrail("/settings")` — `"Workspace"` → `"Preferences"`.
- `navigation-shell.test.tsx`: the rendered group heading `Protection` → `Personal protection`.

No other assertion was weakened. Route lists, labels for the nine destinations, active matching and
breadcrumb behaviour are still asserted.

---

## Part B — Settings

### 1. Structure

`/settings` is now six labelled sections with a sticky anchor nav at the top. Each section is a
`<section>` with `aria-labelledby` pointing at its heading, and a `scroll-mt-24` offset so anchored
navigation does not hide the title under the topbar.

| Section | Contents |
| --- | --- |
| **Notifications** | Three preference switches (air quality alerts, routine reminders, weekly impact). Explicit "Preferences only" badge and a sentence stating no channel is connected in this build. Counter shows `n of 3 enabled`. |
| **Data sources and methods** | What each surface would use: air quality (Open-Meteo/CAMS ENSEMBLE, model data, not a sensor), severity index (CPCB 2014, maximum sub-index, US/EU shown separately), Copilot (server-side, key never in the browser, fallback labelled), freshness (observed/fetched/age/stale from the provider). Map attribution and the factor registry are named. |
| **Local data** | Per-store inventory with live counts: saved locations, SmartRoutine activities, impact log, IndoorShield checklist, travel preferences, notification preferences. Each row has a two-step Clear button (armed for 5 seconds, then confirm). The family profile is explicitly called out as server-side under an anonymous session, with a link to manage it. |
| **Privacy** | No account required; anonymous session token hashed server-side; health flags optional and consent-gated; local-first stores; coordinates rounded to two decimals; no advertising, analytics or third-party tracking script. |
| **Preferences** | Where the other preference surfaces live: alert delivery, travel/commute, household activity preferences, language/locale (English (India) only, `en-IN` formatting). Each links to its real page. |
| **Accessibility** | Working **Reduce motion** switch, WCAG 2.2 AA target badge, and four factual notes (keyboard, focus visibility, colour never the only signal, motion and zoom) plus an explicit statement of the build's testing limits. |

### 2. Reduce motion — a real control, not a mock

- `useMotionPreference()` reads and writes `saans.v1.reduceMotion` through `useSyncExternalStore`.
- Writing the preference sets `document.documentElement.dataset.reduceMotion` immediately and
  dispatches a `saans:motion-preference` event so every subscribed control updates.
- `globals.css` collapses animation and transition durations to `0.01ms` for
  `[data-reduce-motion="true"]`, independently of the OS `prefers-reduced-motion` query. Both paths
  can disable motion; neither can re-enable it against the OS setting.
- `MotionPreference` is mounted in the root layout so a stored preference applies before the first
  painted interaction.

### 3. What Settings deliberately does not do

- It does not claim notifications are delivered — there is no delivery channel.
- It does not expose secrets, keys or tokens. The Copilot section states the model key stays on the
  server and no browser request goes to the model provider.
- It does not offer an export, because the backend does not expose one.
- It does not show a "delete account" action, because there is no account.

### 4. Clearing data

Clearing is intentionally a two-step interaction: the first click arms the button ("Confirm clear"),
a second click within five seconds performs the removal; otherwise it disarms. Disabled when the
store is already empty. This prevents a single stray click from destroying a routine or impact log,
and it is consistent across all six stores.

### 5. Responsive behaviour

- Anchor nav wraps to multiple rows on narrow screens; each chip is a full tap target.
- Store rows use `flex-wrap` so the Clear button drops below the label rather than clipping.
- The notifications list keeps the switch on the right at 320 px, with `aria-labelledby` and
  `aria-describedby` intact.
- No horizontal overflow at any tested width (see `responsive-ui-verification.md`).
