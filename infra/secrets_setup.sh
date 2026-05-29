#!/usr/bin/env bash
# Store DATABASE_URL in Secret Manager for Cloud Run.
set -euo pipefail

PROJECT="${GCP_PROJECT:-jaybel-dev}"
SECRET_DB_URL="${SECRET_DB_URL:-jaybel-db-url}"
SECRET_DB_PASSWORD="${SECRET_DB_PASSWORD:-jaybel-db-password}"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "Set DATABASE_URL (Cloud SQL socket format) before running." >&2
  echo "Example: postgresql://jaybel:PASS@/jaybel_sales_app?host=/cloudsql/jaybel-dev:us-central1:jaybel-sales-db" >&2
  exit 1
fi

gcloud services enable secretmanager.googleapis.com --project="$PROJECT"

if gcloud secrets describe "$SECRET_DB_URL" --project="$PROJECT" &>/dev/null; then
  echo -n "$DATABASE_URL" | gcloud secrets versions add "$SECRET_DB_URL" \
    --project="$PROJECT" --data-file=-
else
  echo -n "$DATABASE_URL" | gcloud secrets create "$SECRET_DB_URL" \
    --project="$PROJECT" --replication-policy=automatic --data-file=-
fi

if [[ -n "${JAYBEL_DB_PASSWORD:-}" ]]; then
  if gcloud secrets describe "$SECRET_DB_PASSWORD" --project="$PROJECT" &>/dev/null; then
    echo -n "$JAYBEL_DB_PASSWORD" | gcloud secrets versions add "$SECRET_DB_PASSWORD" \
      --project="$PROJECT" --data-file=-
  else
    echo -n "$JAYBEL_DB_PASSWORD" | gcloud secrets create "$SECRET_DB_PASSWORD" \
      --project="$PROJECT" --replication-policy=automatic --data-file=-
  fi
fi

SA="${CLOUD_RUN_SA:-115724636423-compute@developer.gserviceaccount.com}"
for SEC in "$SECRET_DB_URL" "$SECRET_DB_PASSWORD"; do
  gcloud secrets add-iam-policy-binding "$SEC" \
    --project="$PROJECT" \
    --member="serviceAccount:${SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet 2>/dev/null || true
done

echo "Secrets ready: $SECRET_DB_URL (and optionally $SECRET_DB_PASSWORD)"
