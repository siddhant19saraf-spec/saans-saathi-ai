# SAANS SAATHI AI — Deployment Guide

## Architecture

```mermaid
graph TD
    subgraph GitHub
        direction LR
        G[Source Code] -->|PRs & CI| G
    end
    
    subgraph Render
        direction LR
        R1[FastAPI Backend] -->|POSTGRES| R2[PostgreSQL]
        R1 -->|GET/POST| R3[Vercel Frontend]
    end
    
    subgraph Vercel
        direction LR
        V1[Next.js Frontend] -->|API calls| R1
        V1 -->|Static assets| CDN
    end
    
    subgraph Google Cloud
        direction LR
        G1[Gemini API] -->|REST calls| R1
    end
```

## Production Configuration

### Environment Variables

| Variable | Required | Description | Source |
|---|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (asyncpg format) | Render/self-hosted |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key | Google Cloud Console |
| `GEMINI_MODEL` | ✅ | Gemini model name (e.g., `gemini-1.5-flash`) | Hardcoded or env |
| `APP_ENV` | ✅ | Environment: `development`/`production` | `production` |
| `FRONTEND_ORIGIN` | ✅ | Production frontend URL (for CORS) | Vercel domain |
| `SECRET_KEY` | ✅ | FastAPI secret key | Generate with `os.urandom(32)` |
| `ALLOWED_HOSTS` | ✅ | Comma-separated list | Render domain, Vercel domain |

### Optional Variables

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `saans-saathi-ai` | Application name |
| `APP_VERSION` | `1.0.0` | Application version |
| `COPILOT_MESSAGES_PER_HOUR` | `20` | Rate limit for copilot |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate limit window |

### .env.example (committed to repo, no real secrets)

```dotenv
# Production Environment Variables
# ================================
# Never commit real secrets; use platform secret management instead.

DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
APP_ENV=production
FRONTEND_ORIGIN=https://your-app.vercel.app
SECRET_KEY=changeme-generate-with-os-urandom32
ALLOWED_HOSTS=your-app.onrender.com,https://your-app.vercel.app
APP_NAME=saans-saathi-ai
APP_VERSION=1.0.0
```

## Backend Deployment (Render)

### Startup Command

```
gunicorn app.main:create_app --worker-class uvicorn.workers.asyncio.UvicornWorker --host 0.0.0.0 --port $PORT
```

### Build Command

No build step (Python application). Alternatively:

```
pip install -r requirements.txt
```

### Python Runtime

- **Version**: `3.13`
- **Runtime**: `python-3.13`

### Port

- **Port**: `$PORT` (provided by Render, typically `8080`)

### PostgreSQL on Render

- Add PostgreSQL service in Render dashboard
- The `DATABASE_URL` will be auto-populated by Render
- Connection pooling is handled by SQLAlchemy `AsyncSession`

### Health Check Endpoint

```
GET /api/v1/health
```

Response example:
```json
{
  "status": "ok",
  "service": "saans-saathi-ai",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": "ok",
    "ai_provider": "configured",
    "air_quality_provider": "configured"
  }
}
```

### Rollback Procedure

1. Previous stable version is tagged in git: `git tag v1.0-stable`
2. Deploy previous version: Render dashboard > Deploys > Manual deploy
3. Or revert to previous commit: `git checkout v1.0-stable && git push render main`

## Frontend Deployment (Vercel)

### Root Directory

```
../frontend
```

### Build Command

```
npm run build
```

### Output Directory

```
.out
```

### Node.js Version

```
18.x
```

### Environment Variables (Vercel Dashboard)

| Variable | Value | Description |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://your-backend.onrender.com` | Backend API base URL |
| `APP_ENV` | `production` | Environment |
| `SECRET_KEY` | *generated* | Not for frontend use |

### Important: Never Set in Vercel

- `GEMINI_API_KEY` — not needed on frontend
- Database credentials — never expose to browser
- `FRONTEND_ORIGIN` — use `NEXT_PUBLIC_API_BASE_URL` instead

### Routing

- All routes handled by Next.js app router
- `/*` catch-all redirects to `/` if needed
- No `_next/*` paths visible to users

### Rollback Procedure

1. In Vercel dashboard: Deploys > Select previous deploy > "Rollback"
2. Or: Create a new deploy from a previous commit tag
3. Vercel automatically preserves deployment history (last 15)

## Database (PostgreSQL)

### Production Setup

- **Platform**: Render (managed) or self-hosted AWS RDS/Azure PostgreSQL
- **Connection**: `postgresql+asyncpg://` format
- **SSL/TLS**: Enabled by default on managed services
- **Connection Pooling**: SQLAlchemy `AsyncSession` with `expire_on_commit=False`
- **Backups**: Automated daily backups (managed service) or `pg_dump` weekly
- **Restricted Access**: VPC security groups, IP allowlists if self-hosted

### Migration Execution

Migrations are executed automatically via Alembic on startup. Ensure:

1. `DATABASE_URL` is set before first startup
2. `alembic upgrade head` has been run locally
3. No `create_all()` usage in production (handled by Alembic)

### Verification Steps

```bash
# 1. Verify connection
psql "postgresql+asyncpg://user:password@host:port/dbname" -c "SELECT 1";

# 2. Verify migrations
alembic upgrade head

# 3. Verify tables
python -c "
from app.models.base import Base
from sqlalchemy import create_engine
engine = create_engine('postgresql+asyncpg://url')
Base.metadata.create_all(bind=engine)  # Should be idempotent
"
```

## Gemini AI Integration

### Configuration

- `GEMINI_API_KEY`: From Google Cloud Console
- `GEMINI_MODEL`: Typically `gemini-1.5-flash` or `gemini-1.5-pro`
- Timeout: 12 seconds per request
- Max retries: 2 (bounded, no infinite loops)

### Failure Behavior

- Graceful fallback to deterministic answer
- Source标记 as `deterministic` when fallback used
- No crash; always returns valid `CopilotAnswer`
- Rate limit (429) handled with retry-after support

### Production Test

```bash
# Verify Gemini is configured
python -c "
from app.core.config import Settings
settings = Settings()
print(f'APP_ENV: {settings.app_env}')
print(f'AI configured: {settings.ai_configured}')
print(f'GEMINI_MODEL: {settings.gemini_model}')
"
```

## CORS Configuration

### Production Origins

```
Allow origins:
- https://your-app.vercel.app
- https://your-app.onrender.com

Do NOT use wildcard `*` for authenticated requests.
```

### CORS Middleware Settings

```python
app.add_middleware(
    CORSMiddleware,
    allow_origin_references=[],  # or specific origins
    allow_origin_patterns=[
        r"https://\.vercel\.app",
        r"https://\.onrender\.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

## Security Headers (Middleware)

Configured in `app/core/middleware.py`:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy` (optional, can be added via reverse proxy)

## Logging

- Structured JSON logs to stderr
- Log levels: `INFO` in production, `DEBUG` in development
- No PII or secrets in logs
- Request ID correlation via middleware
- Log format example:

```json
{
  "time": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Request processed",
  "request_id": "req-abc123",
  "duration_ms": 145,
  "endpoint": "/api/v1/copilot/chat"
}
```

## API Endpoints (Production)

| Endpoint | Method | Description |
|---|---|---|
| `GET /api/v1/health` | GET | Health check |
| `GET /api/v1/healthz` | GET | Raw health (no schema) |
| `GET /api/v1/air/{id}` | GET | Air quality data |
| `GET /api/v1/family/profile` | GET | Family profile |
| `POST /api/v1/copilot/chat` | POST | Copilot chat |
| `POST /api/v1/copilot/tool-request` | POST | Tool execution |
| `GET /api/v1/impact/methodology` | GET | Methodology docs |
| `GET /api/v1/ecoroute/providers/health` | GET | Provider health |

## Frontend-Backend Communication

```
Frontend (Vercel) → HTTPS → Backend (Render)
All API calls use NEXT_PUBLIC_API_BASE_URL
No secrets in browser environment variables
CORS restricts to production origins only
```

## Database Migrations

```bash
# Run locally before deploy
alembic upgrade head

# Verify
python -c "
from app.models.base import Base
# Tables should already exist from alembic
# create_all() should be idempotent (no errors)
"
```

## Monitoring & Alerting

### Health Check Monitoring

- Platform: Render health check `/api/v1/health`
- Uptime monitor: UptimeRobot or similar
- Alert on: 5xx responses, database disconnect, Gemini API failures

### Log Monitoring

- Platform: Render logs → Papertrail/Datadog/Elastic
- Searchable fields: `request_id`, `endpoint`, `status`, `duration`
- Alert on: Error rate > 5%, latency > 5s, database failures

### Provider Monitoring

- Gemini API: Latency > 10s, rate limit 429
- Air quality: Timeout > 8s, stale data warnings
- Database: Connection pool exhaustion, query failures

## Backup & Recovery

### Database Backups

- **Managed**: Daily automated backups (Render/AWS RDS)
- **Self-hosted**: `pg_dump` weekly, stored in S3/GCS
- **Retention**: 30 days minimum

### Rollback Procedure

1. Identify last known good deployment
2. Frontend: Vercel rollback to previous deploy
3. Backend: Render manual deploy to previous commit
4. Database: Restore from last backup if schema changed
5. Verify all health checks pass

### Secret Rotation

1. Rotate in platform secret management (Render/Vercel/Docker secrets)
2. Update `.env.example` (committed) with new placeholder
3. Update environment variables in platform dashboard
4. Redeploy application
5. Verify no service interruption

## Development → Production Parity

### Environment Variables

| Stage | DATABASE_URL | GEMINI_API_KEY | APP_ENV |
|---|---|---|---|
| Development | local postgresql | test key (or mock) | `development` |
| Test | test database URL | test key | `test` |
| Production | managed PostgreSQL | production key | `production` |

### Docker (Optional)

If containerizing:

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY app/ /app/app/
COPY alembic/ /app/alembic/
EXPOSE 8080
CMD ["gunicorn", "app.main:create_app", "--worker-class", "uvicorn.workers.asyncio.UvicornWorker", "--host", "0.0.0.0", "--port", "8080"]
```

### Environment Parity

- Use same `.env.example` across all stages
- Never commit real secrets
- Platform secrets (Render/Vercel) match `.env.example` structure
- `APP_ENV=production` only in production

## Verification Checklist

### Pre-Deploy

- [ ] All 26 Step 10 tests pass
- [ ] Ruff: All checks passed
- [ ] MyPy: No critical errors
- [ ] Bandit: 0 security issues
- [ ] Frontend: 49 Vitest tests pass
- [ ] Production build: `npm run build` succeeds
- [ ] DATABASE_URL configured (not empty)
- [ ] GEMINI_API_KEY configured
- [ ] FRONTEND_ORIGIN set
- [ ] No secrets in git history
- [ ] .gitignore excludes venv/node_modules/coverage
- [ ] Health endpoint `/api/v1/health` tested
- [ ] CORS configured for production origins

### Post-Deploy

- [ ] Backend service starts
- [ ] Health endpoint returns `ok`
- [ ] Database connection verified
- [ ] API docs accessible (if enabled)
- [ ] Frontend loads at deployed URL
- [ ] API requests from frontend succeed
- [ ] Mobile layout works
- [ ] No browser console errors
- [ ] Gemini integration works (or graceful fallback)
- [ ] CORS preflight requests work
- [ ] Rate limiting active
- [ ] No leaked secrets in logs or responses

## Known Limitations

- Gemini API calls have 12s timeout; may time out on slow networks
- Air quality data is best-effort; stale data may appear (honorably labeled)
- Sustainability baseline is modelled, not measured (explicitly labeled)
- No medical advice or diagnoses provided
- Anonymous calls not persisted to conversation history

---
*Deployment guide generated as part of Step 13 production readiness verification.*