#!/usr/bin/env bash
# Optional: link a Firebase user to an existing row (usually auto-created on first login).
set -euo pipefail

FIREBASE_UID="${1:-}"
EMAIL="${2:-}"
DISPLAY="${3:-Cloud User}"

if [[ -z "$FIREBASE_UID" || -z "$EMAIL" ]]; then
  echo "Usage: scripts/seed-cloud-db.sh FIREBASE_UID email@example.com [display_name]" >&2
  echo "Users are normally created automatically on first Google sign-in." >&2
  exit 1
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "Set DATABASE_URL first." >&2
  exit 1
fi

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<SQL
INSERT INTO users (id, email, display_name, firebase_uid)
VALUES (gen_random_uuid(), '$EMAIL', '$DISPLAY', '$FIREBASE_UID')
ON CONFLICT (firebase_uid) DO UPDATE SET email = EXCLUDED.email, display_name = EXCLUDED.display_name;
SQL

echo "Seeded user for firebase_uid=$FIREBASE_UID"
