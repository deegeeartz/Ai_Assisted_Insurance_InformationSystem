# Temporary Free Hosting Runbook

This runbook captures the recommended temporary/free deployment strategy for this project and the easiest update workflow from GitHub.

## Recommended Topology

- Backend (`FastAPI`): Render free web service (or Fly.io)
- Database (`PostgreSQL`): Neon free tier
- Redis: Upstash free tier
- Frontends (`d2c`, `portal`, `widget`): Vercel (3 projects)

## Why This Split

- Lowest setup friction for this multi-service repo
- Easy GitHub auto-deploy support
- Suitable for demo/hackathon usage

## Required Environment Variables

### Backend

- `POSTGRES_SERVER`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `ENCRYPTION_KEY`
- `GOOGLE_API_KEY`
- `SQL_ECHO=false`
- `EXPOSE_ERROR_DETAILS=false`
- `AUTO_CREATE_TABLES=false`
- `AUTO_SEED_DATA=false`

### Frontends

- `VITE_API_URL=https://<backend-domain>/api/v1`

## Deployment Steps

1. Provision Neon Postgres and copy connection values.
2. Provision Upstash Redis and copy `REDIS_URL`.
3. Deploy backend to Render:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Run migrations: `alembic upgrade head`
5. Deploy frontends on Vercel as three separate projects:
   - `frontend/d2c`
   - `frontend/portal`
   - `frontend/widget`
6. Set `VITE_API_URL` per frontend project.
7. Update backend CORS allowlist with deployed frontend domains.

## Auto-Update (GitHub Push)

- Render: enable auto-deploy on default branch
- Vercel: GitHub integration auto-deploys on push
- Suggested flow: PR -> preview deploy -> merge -> production deploy

## Smoke Test Checklist

- `GET /health` returns healthy
- Auth login/register works
- Underwriting returns decisions
- Simulated payment activates policy
- D2C My Policies loads via `/api/v1/policies/my`
- Compliance endpoints enforce tenant scoping

## Notes

- Free tiers may sleep/cold-start
- Keep secrets only in platform environment settings
- Use migrations in deploy pipeline for schema safety