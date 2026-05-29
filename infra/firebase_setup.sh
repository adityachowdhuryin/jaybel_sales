#!/usr/bin/env bash
# Enable Firebase on jaybel-dev and document Google Sign-In setup.
set -euo pipefail

PROJECT="${GCP_PROJECT:-jaybel-dev}"

echo "Enabling Firebase APIs on $PROJECT ..."
gcloud services enable \
  firebase.googleapis.com \
  identitytoolkit.googleapis.com \
  --project="$PROJECT"

echo ""
cat <<EOF
=== Manual steps (Firebase Console) ===
1. Open https://console.firebase.google.com/ and add project "$PROJECT" (or link existing GCP project).
2. Project settings → General → Your apps → Add Web app.
3. Copy config into frontend/.env.local:
   NEXT_PUBLIC_FIREBASE_API_KEY=...
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=${PROJECT}.firebaseapp.com
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=${PROJECT}
4. Authentication → Sign-in method → Enable Google.
5. Authentication → Settings → Authorized domains → add your Cloud Run frontend host, e.g.:
   jaybel-frontend-xxxxx-uc.a.run.app
6. Set backend env: FIREBASE_PROJECT_ID=${PROJECT}

Redeploy frontend after env vars are set.
EOF
