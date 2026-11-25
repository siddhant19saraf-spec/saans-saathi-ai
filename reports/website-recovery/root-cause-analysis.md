# Root Cause Analysis — SAANS SAATHI AI Website Recovery

**Status:** COMPLETE — root cause confirmed by direct instrumentation  
**Date:** Mon Nov 23 2026  
**Engineer:** Principal Full-Stack / Next.js / FastAPI / DevOps

## Executive summary

The website was **not permanently broken**. All 11 routes return HTTP 200 with complete SSR HTML, and React fully hydrates every route given time for the streaming-shell reveal to fire. The "stuck loading" symptom was an **eager-inspection artifact**: probes ran before `requestAnimationFrame` drove React's `$RT`/`$RV`/`$RB` reveal machinery, leaving `<div hidden id="S:0">` hidden and the root `loading.tsx` fallback visible.

Two genuine configuration defects were also found and fixed:
1. CORS allowlist did not include the production frontend origin (`localhost:3001`), blocking `/api/v1/impact/factors`.
2. `backend/render.yaml` had a duplicate top-level `services:` key (silently dropped the web service) and referenced a non-existent `requirements.txt`.
3. `vercel.json` referenced non-existent `frontend/next.config.js`.

## Detailed root cause chain

### 1. SSR streaming shell (`<div hidden id="S:0">`)

Next.js 16.4.6 renders each route as a streaming shell. The raw HTML for every route contains:
```html
<div hidden id="S:0"><div class="flex min-h-dvh flex-col">...</div></div>
```
plus a root `loading.tsx` fallback (`role="status"`, "Loading content") as a direct `<body>` child. The `hidden`/`display:none` on `#S:0` is **correct SSR behavior** — React is supposed to reveal it after hydration.

### 2. React's inline reveal machinery (the gate)

The served HTML includes an inline script defining:
```js
$RT=performance.now()           // set via requestAnimationFrame
$RB=[]                          // pending boundary reveals
$RV=function(a){...}            // removes fallback, swaps in real content
$RC=function(a,b){...}          // schedules reveal via rAF or setTimeout
$RC("B:0","S:0")                // reveal B:0 (template) into S:0 (content)
```

`$RT` is assigned only inside `requestAnimationFrame(function(){$RT=performance.now()})`. If rAF has not fired, `$RT` stays `undefined`. `$RC` then defers `$RV` via:
```js
setTimeout($RV.bind(null,$RB), 2300 > a && 2000 < a ? 2300 - a : $RT + 300 - a)
```
This depends on `$RT` being a number. With `$RT === undefined`, the reveal stalls: `#S:0` remains `display:none;hidden`, the `loading.tsx` fallback stays visible, and React never claims `#main-content`/`<nav>`.

### 3. Measured evidence of the stall (and recovery)

| Probe | `$RT` | `$RB_len` | `#S:0` hidden | `#main-content` fiber | h1 visible |
|---|---|---|---|---|---|
| Eager (generation 3) | `undefined` | 2 | YES | NO | NO |
| Re-probe same tab (generation 6) | `number` | 0 | NO | YES (w=599) | YES (w=567) |

`$RT` transitioned from `undefined` → `number` and `$RB` drained 2 → 0 purely with elapsed time — **rAF fired and the reveal completed**. No code change was required for this; it is expected asynchronous hydration.

### 4. Why it looked permanently stuck

The browser automation probed immediately after navigation. `tools.browser.wait(condition:"networkidle")` is **not a supported condition** (accepted values: `load`, `text`, `textGone`), and those calls were swallowed with `.catch(()=>{})`. So inspections ran at `document.readyState === "complete"` but **before rAF drove the reveal**. Playwright's auto-retrying `toBeVisible({timeout:20000})` correctly waits and passed 13/13.

## Secondary root causes (genuine defects fixed)

### CORS allowlist gap

`backend/app/core/config.py`:
```python
frontend_url: str = "http://localhost:3000"   # default
allowed_origins: str = ""                      # unset -> empty
...
@property
def cors_origins(self) -> list[str]:
    origins = [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
    return origins or [self.frontend_url]      # falls back to :3000 only
```

Direct probe against running backend (:8000):
| Origin | `Access-Control-Allow-Origin` |
|---|---|
| `http://localhost:3000` | `http://localhost:3000` ✅ |
| `http://localhost:3001` | **(absent)** ❌ — fetch blocked |
| `http://evil.example` | **(absent)** ✅ correctly rejected |

Fix: added `ALLOWED_ORIGINS` and `FRONTEND_URL` to `backend/render.yaml` (deployment origins). For local prod testing, `ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001`.

### `backend/render.yaml` — duplicate `services:` key

`yaml.safe_load(render.yaml)` returned `{'services': [...]}` with **only the `db` postgresql service** — the backend web service was silently dropped by the duplicate key. Also `buildCommand: pip install -r requirements.txt` referenced a file that does not exist (project declares deps in `pyproject.toml` via hatchling).

Fix: single `services:` list containing both `saans-saathi-api` (web) and `db` (postgresql); `buildCommand: pip install .`; added `ALLOWED_ORIGINS`/`FRONTEND_URL` env vars.

### `vercel.json` — wrong Next.js config reference

`builds[0].src` = `frontend/next.config.js` — file does not exist; only `frontend/next.config.ts` exists. Fixed to `frontend/next.config.ts`.

## Hypotheses RULED OUT

| Hypothesis | Evidence | Verdict |
|---|---|---|
| Dev-only bug (Turbopack) | Reproduced identically in `npm run start` production build (:3001) | RULED OUT |
| React 19.3.1 incompatible with Next 16.4.6 | PeerDeps accept `^19.0.0`; installed 19.3.1; hydrates fully | RULED OUT |
| `env.ts` Zod schema rejects `http://localhost:8000` | `z.url({protocol:/^https?$/}).safeParse("http://localhost:8000")` → success | RULED OUT |
| CSP blocking inline scripts | Response headers: no `Content-Security-Policy` | RULED OUT |
| Chunk load failures | All 17 `_next/static/chunks/*.js` loaded, 0 failures | RULED OUT |
| `__next_f.push` missing `[0]` bootstrap | Inline `#3`: `(self.__next_f=self.__next_f||[]).push([0])` present | RULED OUT |
| `app-index.js` throwing "missing bootstrap script" | That throw only fires post-flush when buffer is `undefined`; module ran (patched `push`, `windowLen: 0`) | RULED OUT (red herring) |
| Network failures | 19 requests, 0 failures, 0 ≥400 | RULED OUT |

## Files changed (root cause + fixes)

| File | Change |
|---|---|
| `backend/render.yaml` | Single `services:` list (web + postgresql); `buildCommand: pip install .`; added `ALLOWED_ORIGINS`/`FRONTEND_URL` |
| `vercel.json` | `next.config.js` → `next.config.ts` |

No frontend application code was changed — none was required. Hydration works correctly once rAF drives the reveal.

## Verification after fix

| Suite | Result |
|---|---|
| `npm run build` (Next.js) | PASS — 11 static routes + `_not-found` |
| Vitest | 149 passed / 28 files |
| ESLint | clean |
| `tsc --noEmit` | clean |
| Ruff | clean |
| Black | clean |
| MyPy `app` | clean |
| Bandit | exit 0 |
| Pytest | 280 passed, 0 failed |
| Playwright E2E | 13/13 passed (all routes hydrate, zero errors) |
| Coverage | 78.86% (pre-existing 80% gate fail — documented, not suppressed) |

## Conclusion

Root cause: **eager inspection before React's rAF-driven SSR shell reveal completed** — not a code defect. The website hydrates correctly on all 11 routes. Genuine defects fixed: CORS allowlist gap, `render.yaml` duplicate key + bad build command, `vercel.json` stale config reference.
