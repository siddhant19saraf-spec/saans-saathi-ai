# SAANS SAATHI AI — Security Audit

**Audit date:** 2026-11-21  
**Scope:** Authentication, authorization, CORS, secrets, headers, rate limiting, dependency scanning, secret scanning

---

## Authentication & Authorization

| Control | Implementation | Status |
|---------|---------------|--------|
| Session tokens | Opaque bearer token issued by POST `/api/v1/sessions`; SHA-256 hash stored server-side; token never logged | ✓ |
| Session expiry | `expires_at` timestamp validated on read; expired sessions return null | ✓ |
| Bearer token required | All user-data routes require `Authorization: Bearer <token>`; missing/invalid → 401 | ✓ |
| Profile scoping | Every data access filtered by `profile_id` from the bearer token; cross-profile access → 404 | ✓ |
| Health-data consent | Health flags require explicit `health_consent`; missing → 403 `CONSENT_REQUIRED` | ✓ |
| Session lifecycle | `DELETE /api/v1/sessions/me` clears token and all associated data; `clear()` for local logout | ✓ |
| No passwords | Anonymous session model — no username/password, no OAuth, no account recovery | Documented limitation |

## CORS & Network

| Control | Implementation | Status |
|---------|---------------|--------|
| CORS policy | Wildcard CORS **rejected** in production; specific origins required | ✓ |
| Allowed hosts | Default `localhost,127.0.0.1,testserver`; production must set `ALLOWED_HOSTS` and `FRONTEND_URL` explicitly | ✓ |
| Body size limit | Configured to prevent large-payload abuse | ✓ |
| Security headers | `nosniff`, `DENY` framing (X-Frame-Options), referrer policy, COOP, Permissions-Policy | ✓ |
| Frontend headers | `next.config.ts` sets nosniff, DENY framing, referrer policy, COOP, Permissions-Policy | ✓ |

## Secrets & Credentials

| Control | Implementation | Status |
|---------|---------------|--------|
| Secret scan | `gitleaks` / secret scan found only expected placeholders; no real credentials | ✓ |
| `.env.example` | Tracked with dummy placeholder values only | ✓ |
| No env commits | `.env` not tracked; no real keys in repository | ✓ |
| Gemini API key | Optional; when unset, deterministic fallback used; never logged | ✓ |
| Database credentials | `DATABASE_URL` required in production; never hardcoded | ✓ |
| Frontend env | No API keys exposed to browser; all calls go through Next.js API routes or backend | ✓ |

## Rate Limiting

| Control | Implementation | Status |
|---------|---------------|--------|
| Per-session limits | Session-scoped rate limits on write-heavy routes (`routine-generate`, `family-write`, `impact-write`, `household-write`) | ✓ |
| Per-IP limits | IP-scoped rate limits as secondary protection | ✓ |
| Public endpoints | Rate-limited for `impact-factors`, `impact-methodology` | ✓ |
| AI budget | Daily AI request budget enforced via `ai_budget_allows`; exhausted → deterministic fallback | ✓ |

## Dependency Scanning

| Tool | Result | Status |
|------|--------|--------|
| Bandit | 0 findings | ✓ |
| `pip-audit` | Clean (no known vulnerabilities) | ✓ |
| Frontend `npm audit` | Clean | ✓ |

## Code Security Review

| Area | Finding | Status |
|------|---------|--------|
| SQL injection | SQLAlchemy ORM with parameterized queries; no raw SQL string interpolation | ✓ |
| XSS | Next.js auto-escapes; dangerouslySetInnerHTML not used | ✓ |
| CSRF | Stateless bearer-token API; no cookie-based auth | ✓ |
| Path traversal | No file upload or dynamic file serving | ✓ |
| Logging | No secrets, tokens, or PII logged; request IDs for tracing | ✓ |
| Error messages | Generic client-facing messages; detailed errors logged server-side only | ✓ |

## Gaps / Limitations

| Area | Detail |
|------|--------|
| Production deployment | Cannot verify CORS origins, ALLOWED_HOSTS, or DATABASE_URL in production without account access |
| Penetration testing | No external pen test performed; limited to static analysis and dependency scanning |
| OAuth / SSO | Not implemented; anonymous session model only |
| MFA | Not implemented |
