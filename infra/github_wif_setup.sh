#!/usr/bin/env bash
# Workload Identity Federation for GitHub Actions → GCP (keyless deploy).
set -euo pipefail

PROJECT="${GCP_PROJECT:-jaybel-dev}"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"
POOL="${WIF_POOL:-github-pool}"
PROVIDER="${WIF_PROVIDER:-github-provider}"
SA_NAME="${GITHUB_DEPLOY_SA:-github-deploy}"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
REPO="${GITHUB_REPO:-adityachowdhuryin/jaybel_sales}"

gcloud services enable iamcredentials.googleapis.com --project="$PROJECT"

if ! gcloud iam workload-identity-pools describe "$POOL" \
  --location=global --project="$PROJECT" &>/dev/null; then
  gcloud iam workload-identity-pools create "$POOL" \
    --location=global --project="$PROJECT" \
    --display-name="GitHub Actions"
fi

if ! gcloud iam workload-identity-pools providers describe "$PROVIDER" \
  --workload-identity-pool="$POOL" --location=global --project="$PROJECT" &>/dev/null; then
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
    --location=global --project="$PROJECT" \
    --workload-identity-pool="$POOL" \
    --display-name="GitHub" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com"
fi

if ! gcloud iam service-accounts describe "$SA_EMAIL" --project="$PROJECT" &>/dev/null; then
  gcloud iam service-accounts create "$SA_NAME" \
    --project="$PROJECT" \
    --display-name="GitHub Actions deploy"
fi

for ROLE in roles/run.admin roles/artifactregistry.writer roles/cloudbuild.builds.editor roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE" --quiet
done

gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --project="$PROJECT" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${REPO}"

PROVIDER_FULL="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}"

echo ""
echo "Add these GitHub repository secrets:"
echo "  GCP_PROJECT_ID=$PROJECT"
echo "  GCP_WORKLOAD_IDENTITY_PROVIDER=$PROVIDER_FULL"
echo "  GCP_SERVICE_ACCOUNT=$SA_EMAIL"
