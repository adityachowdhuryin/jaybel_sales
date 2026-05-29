# Cloud deployment (no local dependencies)

Fully hosted stack on **jaybel-dev**:

| Component | Service |
|-----------|---------|
| UI | Cloud Run `jaybel-frontend` |
| API | Cloud Run `jaybel-sales-api` |
| App DB | Cloud SQL `jaybel-sales-db` |
| Analytics | BigQuery + Vertex AI Agent Engine |

## One-time setup

```bash
# 1. Cloud SQL
export JAYBEL_DB_PASSWORD='your-secure-password'
./infra/cloud_sql_setup.sh

# 2. Run migrations
export DATABASE_URL='postgresql://jaybel:PASSWORD@/jaybel_sales_app?host=/cloudsql/jaybel-dev:us-central1:jaybel-sales-db'
# Or use Cloud SQL Auth Proxy locally, then:
./scripts/migrate-db.sh

# 3. Secret Manager
export DATABASE_URL='...'  # same as above
./infra/secrets_setup.sh

# 4. Firebase (console + script)
./infra/firebase_setup.sh
# Enable Google sign-in; copy Web app config to frontend/.env.local

# 5. GitHub Actions (optional)
./infra/github_wif_setup.sh
# Add secrets to GitHub repo per script output
```

## Deploy

```bash
./scripts/deploy-backend.sh

export NEXT_PUBLIC_API_BASE_URL='https://jaybel-sales-api-....run.app'
./scripts/deploy-frontend.sh \
  --api-url "$NEXT_PUBLIC_API_BASE_URL" \
  --firebase-api-key 'AIza...'

# Update backend CORS (commas in origins are OK — script uses gcloud ^|^ delimiter)
./scripts/deploy-backend.sh --cors 'https://jaybel-frontend-....run.app,http://localhost:3000'
```

After deploy, open the frontend URL. With Firebase (default), sign in with Google. If OAuth fails with **unauthorized domain**, add the Cloud Run hostname under **Firebase → Authentication → Authorized domains**.

**Open without login (anyone with the link):**

```bash
./scripts/deploy-backend.sh --no-auth --cors 'https://jaybel-frontend-....run.app,http://localhost:3000'
./scripts/deploy-frontend.sh --no-auth --api-url 'https://jaybel-sales-api-....run.app'
```

This disables Firebase on the UI and `AUTH_DISABLED` on the API (shared default user). **Not recommended for sensitive production data.**

## Local development (optional)

- Postgres: `docker compose up -d`
- Backend: `AUTH_DISABLED=true` in `backend/.env`
- Frontend: omit `NEXT_PUBLIC_FIREBASE_API_KEY` to skip login locally

Agent Engine and BigQuery always run in GCP.

## Live URLs (jaybel-dev)

| Service | URL |
|---------|-----|
| UI | https://jaybel-frontend-oubkdpt52a-uc.a.run.app |
| API | https://jaybel-sales-api-oubkdpt52a-uc.a.run.app |
| Cloud SQL | `jaybel-sales-db` (PostgreSQL 16, db-f1-micro) |

Sign in with Google at the UI URL. Firebase authorized domain `jaybel-frontend-oubkdpt52a-uc.a.run.app` must be listed (Authentication → Settings).
