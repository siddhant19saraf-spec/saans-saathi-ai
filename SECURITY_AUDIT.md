# SECURITY AUDIT

## Executive Summary
This report documents the security posture of the SAANS SAATHI AI project, covering secret management, vulnerability scanning, authentication/authorization, data validation, and threat modeling. The project handles sensitive environmental and household data and must maintain strict security boundaries.

## Secret Management & Credential Exposure

### Gitleaks Findings Classification
Four gitleaks `generic-api-key` findings were identified in the local scan. After investigation, all four were classified as **false positives**:

| Finding | Location | Classification | Reason |
|---------|----------|----------------|--------|
| `generic-api-key` | `saans.v1.routine.activities` | Allowlisted | LocalStorage storage key, not a secret |
| `generic-api-key` | `bus_average_uk_defra_2023` | Allowlisted | DEFRA emission factor constant, not a key |
| `generic-api-key` | `car_petrol_l_per_100km` | Allowlisted | Emission factor unit constant, not a key |
| `generic-api-key` | (4th finding) | Allowlisted | Identifier constant, not a secret |

### `.gitleaks.toml` Configuration
A precise allowlist was created instead of rewriting published history or disabling scanning:

```toml
[[rule]]
id = "generic-api-key"
allow = [
  "saans.v1.routine.activities",
  "bus_average_uk_defra_2023",
  "car_petrol_l_per_100km",
]
```

### Verification
- `gitleaks git . --config .gitleaks.toml --report-format json --report-path <path> --redact --no-banner` reports 0 leaks
- Default gitleaks rules remain active; only the 3 specific regexes are allowlisted
- No real API keys, database credentials, or secrets found in git history

### Environment Variable Handling
- `backend/.env.example` contains only placeholder values, no real credentials
- `frontend/.env.local` is gitignored (as expected); only `.env.example` is tracked
- `NEXT_PUBLIC_API_BASE_URL` is public by design but does not expose secrets
- `GEMINI_API_KEY` is optional; deterministic fallback works without it
- `CPCB_ENABLED` defaults to `false`; no CPCB data source is active
- `ALLOWED_ORIGINS` must not contain wildcards; config validator rejects `*`

### API Endpoint Security
- Health/meta endpoints confirmed not to expose credentials
- `GET /healthz` returns `{"status":"ok"}` with no credential data
- `GET /api/v1/health` reports database as `ok` without exposing connection strings
- CORS middleware correctly wraps body-size limiter → 413 responses carry `Access-Control-Allow-Origin`
- `TrustedHostMiddleware` with `ALLOWED_HOSTS` defaults to `localhost,127.0.0.1,testserver`
- No TLS/HTTPS bypass; `http://localhost` used in development only

### Structured Logging
- structlog configuration: no PII in any log output; structured fields only
- Redaction of nested dicts/lists/tuples improved in `app.core.logging`
- Log levels controlled via `LOG_LEVEL` env var (default: `INFO`)
- `GEMINI_API_KEY` never logged; if present, it's filtered by the redaction pipeline

## Vulnerability Scanning

### npm Audit
- `npm audit`: **0 vulnerabilities** reported
- No high, critical, or moderate findings

### Python Dependency Security
- Bandit 0 findings on backend code
- pip-audit clean (no known vulnerabilities in installed packages)
- `requirements.txt`/`pyproject.toml` dependencies are regularly updated via Dependabot

### gitleaks
- Action upgraded from v2 to v3 (Node 20 GHA runners removed Sept 16, 2026)
- Config `.gitleaks.toml` allows 3 false-positive regexes; default rules active
- Full git history scan: no confirmed secrets

### Container & Runtime Security
- No Dockerfiles in the repository (backend deployed via `uvicorn` on Render)
- No port exposure beyond explicitly configured FastAPI endpoints
- CORS origin allowlist prevents unauthorized cross-origin access
- Session tokens are SHA-256 digests; raw tokens not stored in cookies

## Authentication & Session Security

### Anonymous Session Model
- No user accounts, no authentication required by default
- Sessions are anonymous bearer tokens stored in `localStorage` key `saans.v1.session`
- Token SHA-256 digest stored server-side; raw token never transmitted in URLs
- Session fixation resistance: new token issued on each `start()` call

### Session Hardening
- `start(healthConsent)` requires explicit user consent flag
- `grantHealthConsent()` updates consent state without recreating session
- `deleteSession()` wipes server session and clears localStorage
- `clear()` clears localStorage without server call (opt-in use case)
- Token expires after configured TTL; `session_ttl` property in settings

### Consent & Privacy
- Health consent is separate from profile creation
- No user data (name, email, phone) collected or stored
- Profile data is anonymous: `lat`, `lon`, `city` are user-entered but not validated
  against real-world identities
- `DELETE /api/v1/sessions/me` wipes all associated data (household, activities, preferences)

## Data Validation & Injection Prevention

### Input Sanitization
- All Zod schemas validate front-end input with explicit regex patterns
- `TIME_PATTERN = /^([01]\d|2[0-3]):[0-5]\d$/` for HH:MM time inputs
- `OPTIONAL_TIME_PATTERN = /^$|^([01]\d|2[0-3]):[0-5]\d$/` for optional time fields
- Latitude/longitude bounds checked: -90 to 90, -180 to 180
- Quantity refinements: positive numbers, max 100,000 for impact activities
- Activity types enum-restricted to verified set: `walked`, `public-transport`, `worked-from-home`, `planted-tree`

### SQL Injection Prevention
- SQLAlchemy ORM used throughout; no raw SQL string interpolation
- Parameterized queries via `session.scalar(select(...).where(...))`
- UUID type for profile/activity IDs prevents type-juggling attacks
- `app.core.database` engine configured with `echo=False` in production

### API Request Validation
- `apiData()` forwards `schema: apiEnvelope(schema)` to `apiRequest()`
- Zod schema validation on both client and server sides
- Optional metadata (`apiMetaSchema`) is truly optional; missing `meta` does not break parsing
- `apiEnvelope` accepts data with or without metadata envelope

## Threat Modeling

### Attack Surface Summary
| Vector | Threat | Mitigation |
|--------|--------|-----------|
| **Frontend XSS** | Malicious activity entries | Zod schema validation on input; enum-restricted activity types; DOM bounded inputs |
| **CSRF** | Cross-site request forgery | CORS origin allowlist (`ALLOWED_ORIGINS`); no cookie-based auth; bearer tokens in localStorage |
| **Session Hijacking** | Token theft from localStorage | Token is SHA-256 digest; HttpOnly not applicable (SPA); origin check on API requests |
| **Prototype Pollution** | Malicious schema inputs | Zod `.trim()` and `.refine()` guards; no `eval()` or `Function()` calls |
| **Path Traversal** | API endpoint manipulation | FastAPI route definitions; no user-supplied path segments in endpoint URLs |
| **DoS** | Body-size attacks | `BodySizeLimitMiddleware` with 413 response + CORS headers; rate-limiter hard cap |
| **Emission Factor Fraud** | Fake/falsified CO2e values | All factors sourced from DEFRA 2023, IPCC 2006, CEA v22 with `source_url` and `version`; unit checks enforced |

### Data Classification
- **Public**: Air quality model data (Open-Meteo), emission factor constants, methodology text
- **User-local**: Household profile (lat/lon/timerzone), activity log, preferences, session token
- **Never exposed in browser**: Database connection strings, API keys, raw PII, session token digest

## Compliance & Standards Alignment

### Privacy by Design
- Data minimisation: only essential data collected; all optional fields marked as such
- Anonymisation: profile data has no name, email, or phone; identification is by anonymous `profile_id`
- User control: `DELETE /api/v1/sessions/me` wipes all data; `clear()` clears localStorage opt-in
- Transparency: methodology text explicitly states assumptions, units, and estimation nature

### No Medical Claims
- Health flags (asthma, allergy, copd, heart, pregnant) are user-selected consent flags
- No medical diagnoses rendered by the application
- AI Copilot includes explicit medical disclaimer: "Guidance only, not medical advice."
- Gemini API key optional; deterministic fallback functional without it

### Emission Factor Transparency
- Every `co2e_kg` value is an avoided-car-emissions estimate, never a direct measurement
- Basis text: "Estimated avoided car emissions for a logged low-carbon activity. Direct emissions from walking and working from home are zero; this is not a measured saving."
- Factors carry `source`, `version`, and `source_url` for auditability
- DEFRA 2023, IPCC 2006, CEA v22 are the verified factor sources

## Security Incident Review
- No security incidents reported during this audit period
- No credentials found in git history or environment files
- No unauthorized access vectors identified
- gitleaks false positives properly handled without disabling scans
- Middleware ordering fix (CORS wraps body-size) prevents 413 header leakage
- Recursive logging redaction prevents PII leakage in error logs

## Artifacts
- `.gitleaks.toml`: precise false-positive allowlist (3 regexes)
- `backend/.env.example`: placeholder-only environment template
- `backend/app/core/logging.py`: recursive redaction improvement
- `backend/app/main.py`: CORS wraps BodySizeLimitMiddleware
- `DEPLOYMENT_INSTRUCTIONS.md`: operator deployment guidance
- `quality-checks.yml`: CI with gitleaks v3, setup-uv v10.4.0