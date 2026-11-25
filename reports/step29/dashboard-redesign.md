# Dashboard Redesign — Step 29

## 1. Before

The dashboard was a vertical stack of five panels: a plain title block, `Current conditions`, a
provider-AQI card, a pollutant bar chart, `Source & freshness`, `Trends & forecast`, `Personalised
insights` and `Smart actions`. Every panel used the same card weight, so nothing led the eye. There
was no greeting, no household/routine/indoor/impact summary, no quick actions and no recent activity.
With no saved location the page collapsed to a single centred "Choose a location to begin" card and
most of the viewport was empty.

Baseline evidence: `step29-before/dashboard-1440.png` and `step29-before/dashboard-seeded-1440.png`.

## 2. After — composition

`frontend/src/components/dashboard/dashboard-view.tsx` now composes:

```
DashboardHero        welcome + location + live CPCB status + freshness + provenance
QuickActions         four task entries
CurrentAirSection    AQI dial, pollutant grid, provider AQI, source & freshness
DailyPulse           family readiness · routine · indoor · impact
RecentActivity       latest routine and impact entries
AnalyticsSection     trends & forecast (provider-only)
InsightsPanel        household context and next actions
```

Sections are separated by a consistent 36 px rhythm (`space-y-9`), each opened by `SectionHeader`
with a title, a one-line description and an optional action.

## 3. The twelve required elements

| # | Requirement | Implementation | Honesty rule |
| --- | --- | --- | --- |
| 1 | Personalised welcome | `DashboardHero` greeting (morning/afternoon/evening, computed only after mount) with the selected place in the headline and the full date as a status chip | Greeting falls back to "Welcome" until mounted, so SSR and client markup agree |
| 2 | Selected location | Location name in the hero headline, rounded coordinates chip, plus the global location switcher in the topbar | Coordinates are rounded to two decimals; a map point is never called a station |
| 3 | Current air-quality status | Hero status panel: large tabular CPCB value, `SeverityBadge` with category and range, severity summary sentence, dominant pollutant and coverage | No AQI is rendered unless the provider returned one; otherwise the panel says "No CPCB index this hour" with the provider's reason |
| 4 | Pollutant summary | `CurrentAirSection` pollutant grid with per-pollutant unit and "last reported" values | Only reported pollutants appear; missing ones are shown as not reported, never filled |
| 5 | Data freshness | Fresh/stale `StatusBadge` with age in minutes in the hero; observed/fetched times and stale flag in the provenance panel | Age comes from the response's `age_minutes` and `stale` fields, not a client-side guess |
| 6 | Source provenance | Source-type chip (ground observation / historical observation / model-based forecast), provider, model and attribution list in `ProvenancePanel` | Model data is labelled "Model-based forecast" and explicitly "not a monitoring station" |
| 7 | Family readiness | `DailyPulse` metric: member count, health-flag note, link to Family intelligence | Empty state reads "No profile yet"; no household risk score is invented |
| 8 | Daily routine overview | `DailyPulse` routine metric (count + first activity) and "Today's routine" list in `RecentActivity` | Counts come from the local store; no exposure score is attached to a time slot |
| 9 | Indoor protection status | `DailyPulse` indoor metric showing `completed/total` and percent of the household checklist | Checklist completion is labelled as an assessment, not a measurement |
| 10 | Sustainability impact summary | `DailyPulse` impact metric (entry count) and "Latest impact entries" list with quantities and units | Quantities only — no CO₂e total, no "kg saved" badge |
| 11 | Quick actions | `QuickActions`: add/change location, open air intelligence, plan a routine, log an impact entry | Actions are links to real routes, not disabled placeholders |
| 12 | Recent activity | `RecentActivity`: latest three routine items and three impact entries, with an explicit empty state | Empty state explains what will appear and links to both source pages |

## 4. Data-state behaviour

Every data region has four explicit states, and only the success state shows numbers:

| State | Rendering |
| --- | --- |
| Loading / idle | Skeleton blocks with `aria-busy="true"` and a polite live region ("Loading current air quality") |
| Unavailable / error | `CloudOff` icon, the provider's message, and a Retry button wired to the resource's `retry` |
| Success with missing sub-values | The specific sub-value is omitted with a reason (e.g. partial CPCB coverage note) |
| Empty local store | `MetricCard` empty label ("No profile yet", "No activities yet") or `EmptyState` with next steps |

`MetricCard` treats `null`, `undefined` and `""` as "no value" and renders the empty label, so a
missing measurement can never render as `0`.

## 5. Visual hierarchy

Three levels replaced the previous single level:

1. **Hero** — `surface-hero` (white with a soft emerald radial glow), 16 px radius, `shadow-card`,
   two-column layout at `lg`; the only surface with a gradient, and it is a 10% tint.
2. **Section cards** — white, hairline border, `shadow-card`, 16 px radius.
3. **Nested blocks** — `surface-muted` or a bordered inner panel, no shadow.

Typography carries the rest: 4xl tabular metric in the hero, 2xl metrics in `MetricCard`, `text-sm`
body, `text-xs` metadata, uppercase 11 px labels for eyebrows only.

## 6. Responsive behaviour

- Hero: single column below `lg`; the status panel moves below the copy and keeps full width.
- Quick actions: 2 columns at `sm`, 4 at `xl`.
- Daily pulse: 1 → 2 (`sm`) → 4 (`xl`) columns.
- Recent activity: stacked below `lg`, two columns above.
- Pollutant grid: 2 columns at 320 px, 3 at `sm`, 6 at `lg`; values use tabular numerals so they do
  not reflow.
- No horizontal scrolling at 320 px; verified in `responsive-ui-verification.md`.

## 7. Preserved behaviour

- All test-locked text and regions remain: `Current conditions`, "Choose a location to begin",
  "Add coordinates", "Pick on the map", "No CPCB index this hour", "Something went wrong",
  "Retry", provenance labels and the unavailable-state copy.
- The location gate still owns the no-location state; the dashboard does not render a hero without a
  location.
- `AnalyticsSection` still refuses to draw a chart without a provider response and keeps its
  "Something went wrong" + Retry path.
- No new network calls were added to the dashboard beyond the existing current-air query.

## 8. Result

The dashboard now answers four questions above the fold — where am I, how is the air, how fresh is
that answer, and what should I do next — and continues into household, routine, indoor and impact
context. All of it is driven by provider responses or local stores; nothing is synthesised.
