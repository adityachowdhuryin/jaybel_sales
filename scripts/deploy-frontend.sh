#!/usr/bin/env bash
# Build and deploy Next.js frontend to Cloud Run.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${GCP_PROJECT:-jaybel-dev}"
REGION="${GCP_REGION:-us-central1}"
SERVICE="${CLOUD_RUN_FE_SERVICE:-jaybel-frontend}"
IMAGE="${ARTIFACT_FE_IMAGE:-us-central1-docker.pkg.dev/${PROJECT}/jaybel/jaybel-frontend}"

API_URL="${NEXT_PUBLIC_API_BASE_URL:-}"
FB_KEY="${NEXT_PUBLIC_FIREBASE_API_KEY:-}"
FB_DOMAIN="${NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN:-${PROJECT}.firebaseapp.com}"
FB_PROJECT="${NEXT_PUBLIC_FIREBASE_PROJECT_ID:-${PROJECT}}"
NO_AUTH=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-url) API_URL="$2"; shift 2 ;;
    --firebase-api-key) FB_KEY="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --no-auth) NO_AUTH=1; FB_KEY=""; FB_PROJECT=""; shift ;;
    -h|--help)
      echo "Usage: scripts/deploy-frontend.sh --api-url URL [--firebase-api-key KEY | --no-auth]"
      exit 0
      ;;
    *) echo "Unknown: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$API_URL" ]]; then
  echo "Required: --api-url" >&2
  exit 1
fi
if [[ "$NO_AUTH" != "1" && -z "$FB_KEY" ]]; then
  echo "Required: --firebase-api-key or --no-auth (open app without login)" >&2
  exit 1
fi
if [[ "$NO_AUTH" == "1" ]]; then
  echo "NOTE: Building without Firebase — visitors go straight to chat (no login)."
fi

AUTH_DISABLED_FLAG="false"
if [[ "$NO_AUTH" == "1" ]]; then
  AUTH_DISABLED_FLAG="true"
fi

gcloud builds submit "$ROOT" \
  --project="$PROJECT" \
  --config="$ROOT/cloudbuild-frontend.yaml" \
  --substitutions="_IMAGE=${IMAGE}:latest,_API_URL=${API_URL},_FB_KEY=${FB_KEY},_FB_DOMAIN=${FB_DOMAIN},_FB_PROJECT=${FB_PROJECT},_GCP_PROJECT=${PROJECT},_GCP_LOCATION=${REGION},_AUTH_DISABLED=${AUTH_DISABLED_FLAG}"

gcloud run deploy "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --image="${IMAGE}:latest" \
  --platform=managed \
  --allow-unauthenticated \
  --min-instances=0

URL="$(gcloud run services describe "$SERVICE" --project="$PROJECT" --region="$REGION" --format='value(status.url)')"
echo ""
echo "Frontend deployed: $URL"
echo "Add to Firebase authorized domains and redeploy backend with:"
echo "  CORS_ORIGINS=$URL scripts/deploy-backend.sh --cors $URL"
