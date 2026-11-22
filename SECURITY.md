# Security Policy

## Supported versions

SAANS SAATHI AI is pre-1.0. Security fixes are applied to the `main` branch only.

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |
| < 0.1   | No        |

## Reporting a vulnerability

Do **not** open a public issue for security problems.

1. Use GitHub's private vulnerability reporting on this repository
   ("Security" tab → "Report a vulnerability").
2. Include: affected endpoint or file, reproduction steps, impact, and any suggested fix.
3. You can expect an acknowledgement within 72 hours and a remediation plan within 7 days.

Please do not test against production infrastructure, run denial-of-service tests, or access data
that does not belong to you. Proof-of-concept work should be limited to a local checkout.

## Secrets

- Real credentials are **never** committed. `.env` files are ignored; only `.env.example` with
  placeholders is tracked.
- Server secrets (`DATABASE_URL`, `GEMINI_API_KEY`) must never be exposed through `NEXT_PUBLIC_*`
  variables or client bundles.
- If a secret is committed by accident, treat it as compromised: revoke it at the provider first,
  then purge it from history. Rotating the key is mandatory; history rewriting alone is not enough.

### Secret scanning

- Enable GitHub **Secret scanning** and **Push protection** for the repository.
- Run a local scan before pushing:

  ```bash
  docker run --rm -v "$PWD:/repo" zricethezav/gitleaks:latest detect -s /repo --no-git
  ```

  If Docker is unavailable, install `gitleaks` and run `gitleaks detect --source . --no-git`.
- CI runs `gitleaks` on every push and pull request (see `.github/workflows/quality-checks.yml`).

## Dependency security

- Direct dependencies are pinned; frontend uses `package-lock.json`, backend uses `uv.lock`.
- CI runs `pip-audit` and `npm audit --omit=dev` and fails on high or critical findings.
- Dependabot is configured for weekly updates of npm, pip and GitHub Actions.

## Application security baseline (current)

- Input validation at every HTTP boundary (Pydantic models with `extra="forbid"`).
- RFC 9457 problem responses with a request ID; no stack traces, SQL, or infrastructure details are
  returned to clients.
- CORS restricted to `FRONTEND_URL`; no wildcard origins.
- Request body limits, per-request timeouts, and rate limiting are introduced with the first
  business endpoints (see `docs/BLUEPRINT.md` §11).
- Logs redact authorization headers, tokens, and API keys.

## Out of scope for the current milestone

The application currently exposes only a health endpoint. Authentication, personal data storage,
and AI integration are not implemented yet; their threat models are documented in
`docs/BLUEPRINT.md` §8 and §11 and will be implemented with tests before those features ship.
