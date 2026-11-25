# Public URL Verification — SAANS SAATHI AI

**Status:** NOT DEPLOYED 
**Date:** Mon Nov 23 2026 
**Engineer:** Principal DevOps

## Current Deployment Status

The SAANS SAATHI AI website is **not currently deployed** to any public hosting provider. No live URL exists.

### Why No Public URL Yet

| Reason | Detail |
|---|---|
| No deployment authorized | No explicit authorization to deploy to Render, Vercel, or any other provider |
| No live services | Frontend and backend are running locally only (`localhost:3000` and `localhost:8000`) |
| Configuration exists but not applied | `render.yaml` and `vercel.json` are correctly configured but not deployed |
| No domain assigned | No custom domain or provider subdomain configured |
| No HTTPS | Would require provider setup (automatic on Vercel/Render) |

### Existing Deployment Configuration (Not Yet Applied)

#### `vercel.json` (if deployed to Vercel)

```json
{
  "version": 2,
  "builds": [
    { "src": "frontend/next.config.ts", "use": "@vercel/next-build" }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "frontend/.next/$1" },
    { "src": "/api/(.*)", "dest": "backend/app/main.py?/$1" }
  ],
  "env": {
    "NEXT_PUBLIC_API_BASE_URL": "https://saans-saathi-api.vercel.app"
  }
}
```

Would deploy the Next.js frontend to Vercel, with API routes proxied to the backend. `NEXT_PUBLIC_API_BASE_URL` would be set to the Vercel backend URL.

#### `render.yaml` (if deployed to Render)

Would deploy:
- **Web service:** `saans-saathi-api` (FastAPI + uvicorn, port `$PORT`)
- **PostgreSQL service:** `db` (managed database, 10GB disk)
- Environment variables: `ALLOWED_ORIGINS`, `FRONTEND_URL`, `DATABASE_URL`, `GEMINI_API_KEY`

Would provide subdomain like `saans-saathi-api.onrender.com` and `saans-saathi-web.onrender.com`.

## Public URL Verdict

**NOT DEPLOYED** — No public URL can be verified because no hosting provider has been used to deploy the application.

### To Deploy and Obtain a Public URL

1. **Authorize a hosting provider** (Render or Vercel, or both)
2. **Set `GEMINI_API_KEY`** in the provider environment variables
3. **Push to the `main` branch** (or trigger manual deploy)
4. **Wait for build to complete**
5. **Verify the provided subdomain**

### Expected Public URLs (after deployment)

| Service | Expected URL Pattern | Provider |
|---|---|---|
| **Frontend** | `https://saans-saathi-web.vercel.app` or `https://saans-saathi-web.onrender.com` | Vercel or Render |
| **Backend API** | `https://saans-saathi-api.vercel.app/api/v1/...` or `https://saans-saathi-api.onrender.com/api/v1/...` | Vercel or Render |
| **Health** | `https://saans-saathi-api.onrender.com/healthz` | Render |
| **API Docs** | Disabled in production (`docs_enabled=False`) | — |

### Public Accessibility Test Checklist

- [ ] Frontend HTTP available (200 on home page)
- [ ] Backend health endpoint responds (200 `{"status":"ok"}`)
- [ ] Frontend communicates with deployed backend (API calls succeed)
- [ ] Seven modules functional on deployed URLs
- [ ] HTTPS works (automatic on Vercel/Render)
- [ ] No critical runtime errors in deployment logs
- [ ] API requests reach the deployed backend (CORS configured)
- [ ] No secrets exposed in public responses

**Current status: NONE of the above can be verified because the application is not deployed.**

## Conclusion

No public URL exists for SAANS SAATHI AI at this time. The application is fully functional on `localhost:3000` (frontend) and `localhost:8000` (backend). To obtain a public URL, a hosting provider must be authorized and the deployment workflow executed.

**No public accessibility claims based on localhost tests alone.** Local verification confirms the application works correctly, but production deployment requires authorized provider setup.