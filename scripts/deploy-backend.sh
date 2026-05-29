#!/usr/bin/env bash
# Build and deploy FastAPI backend to Cloud Run.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${GCP_PROJECT:-jaybel-dev}"
REGION="${GCP_REGION:-us-central1}"
SERVICE="${CLOUD_RUN_API_SERVICE:-jaybel-sales-api}"
IMAGE="${ARTIFACT_IMAGE:-us-central1-docker.pkg.dev/${PROJECT}/jaybel/jaybel-sales-api}"
INSTANCE="${CLOUD_SQL_INSTANCE:-jaybel-sales-db}"
CONNECTION="${PROJECT}:${REGION}:${INSTANCE}"
SA="${CLOUD_RUN_SA:-115724636423-compute@developer.gserviceaccount.com}"
AGENT_ENGINE="${AGENT_ENGINE_RESOURCE:-projects/115724636423/locations/us-central1/reasoningEngines/8991351443894042624}"
SECRET_DB_URL="${SECRET_DB_URL:-jaybel-db-url}"
CORS="${CORS_ORIGINS:-}"
AUTH_DISABLED="${AUTH_DISABLED:-0}"
DEFAULT_USER_ID="${DEFAULT_USER_ID:-00000000-0000-4000-8000-000000000001}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --cors) CORS="$2"; shift 2 ;;
    --no-auth) AUTH_DISABLED=1; shift ;;
    -h|--help)
      echo "Usage: scripts/deploy-backend.sh [--project ID] [--region ID] [--cors ORIGINS] [--no-auth]"
      exit 0
      ;;
    *) echo "Unknown: $1" >&2; exit 1 ;;
  esac
done

gcloud services enable artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com \
  --project="$PROJECT"

if ! gcloud artifacts repositories describe jaybel --location="$REGION" --project="$PROJECT" &>/dev/null; then
  gcloud artifacts repositories create jaybel \
    --repository-format=docker --location="$REGION" --project="$PROJECT"
fi

echo "Building $IMAGE ..."
gcloud builds submit "$ROOT" \
  --project="$PROJECT" \
  --config="$ROOT/cloudbuild-backend.yaml" \
  --substitutions="_IMAGE=${IMAGE}:latest"

# Use | delimiter so CORS_ORIGINS may contain commas (see gcloud --set-env-vars)
ENV_VARS="GOOGLE_CLOUD_PROJECT=${PROJECT}|GOOGLE_CLOUD_LOCATION=${REGION}|AGENT_ENGINE_RESOURCE=${AGENT_ENGINE}|FIREBASE_PROJECT_ID=${PROJECT}"
if [[ -n "$CORS" ]]; then
  ENV_VARS="${ENV_VARS}|CORS_ORIGINS=${CORS}"
fi
if [[ "$AUTH_DISABLED" == "1" ]]; then
  ENV_VARS="${ENV_VARS}|AUTH_DISABLED=true|DEFAULT_USER_ID=${DEFAULT_USER_ID}"
  echo "NOTE: AUTH_DISABLED=true — API accepts requests without Firebase login."
fi

gcloud run deploy "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --image="${IMAGE}:latest" \
  --platform=managed \
  --service-account="$SA" \
  --add-cloudsql-instances="$CONNECTION" \
  --min-instances=1 \
  --allow-unauthenticated \
  --set-secrets="DATABASE_URL=${SECRET_DB_URL}:latest" \
  --set-env-vars="^|^${ENV_VARS}"

URL="$(gcloud run services describe "$SERVICE" --project="$PROJECT" --region="$REGION" --format='value(status.url)')"
echo ""
echo "Backend deployed: $URL"
echo "Set frontend NEXT_PUBLIC_API_BASE_URL=$URL"
