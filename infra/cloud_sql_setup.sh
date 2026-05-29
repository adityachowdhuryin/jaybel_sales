#!/usr/bin/env bash
# One-time: Cloud SQL PostgreSQL for Jaybel Sales Analytics app state.
set -euo pipefail

PROJECT="${GCP_PROJECT:-jaybel-dev}"
REGION="${GCP_REGION:-us-central1}"
INSTANCE="${CLOUD_SQL_INSTANCE:-jaybel-sales-db}"
DB_NAME="${DB_NAME:-jaybel_sales_app}"
DB_USER="${DB_USER:-jaybel}"
TIER="${CLOUD_SQL_TIER:-db-f1-micro}"
# db-f1-micro is the cheapest shared-core tier; requires Enterprise (not Enterprise Plus).
EDITION="${CLOUD_SQL_EDITION:-enterprise}"
# Set JAYBEL_DB_PASSWORD before running, or one is generated and printed.
DB_PASSWORD="${JAYBEL_DB_PASSWORD:-}"

if [[ -z "$DB_PASSWORD" ]]; then
  DB_PASSWORD="$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)"
  echo "Generated DB password (save to Secret Manager): $DB_PASSWORD"
fi

echo "Enabling APIs..."
gcloud services enable \
  sqladmin.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  firebase.googleapis.com \
  --project="$PROJECT"

if ! gcloud sql instances describe "$INSTANCE" --project="$PROJECT" &>/dev/null; then
  echo "Creating Cloud SQL instance $INSTANCE ..."
  gcloud sql instances create "$INSTANCE" \
    --project="$PROJECT" \
    --database-version=POSTGRES_16 \
    --edition="$EDITION" \
    --tier="$TIER" \
    --region="$REGION" \
    --storage-auto-increase \
    --backup-start-time=03:00
else
  echo "Instance $INSTANCE already exists."
fi

if ! gcloud sql databases describe "$DB_NAME" --instance="$INSTANCE" --project="$PROJECT" &>/dev/null; then
  gcloud sql databases create "$DB_NAME" --instance="$INSTANCE" --project="$PROJECT"
fi

echo "Setting user password for $DB_USER ..."
gcloud sql users set-password "$DB_USER" \
  --instance="$INSTANCE" \
  --project="$PROJECT" \
  --password="$DB_PASSWORD" 2>/dev/null || \
gcloud sql users create "$DB_USER" \
  --instance="$INSTANCE" \
  --project="$PROJECT" \
  --password="$DB_PASSWORD"

CONNECTION_NAME="${PROJECT}:${REGION}:${INSTANCE}"
SA_EMAIL="${CLOUD_RUN_SA:-${PROJECT_NUMBER:-115724636423}-compute@developer.gserviceaccount.com}"

echo "Granting Cloud SQL Client to $SA_EMAIL ..."
gcloud projects add-iam-policy-binding "$PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudsql.client" \
  --condition=None \
  --quiet 2>/dev/null || true

SOCKET="/cloudsql/${CONNECTION_NAME}"
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=${SOCKET}"

echo ""
echo "=== Cloud SQL ready ==="
echo "Connection name: $CONNECTION_NAME"
echo "DATABASE_URL (for Cloud Run):"
echo "  $DATABASE_URL"
echo ""
echo "Next: ./infra/secrets_setup.sh  then  ./scripts/migrate-db.sh"
