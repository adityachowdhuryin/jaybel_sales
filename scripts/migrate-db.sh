#!/usr/bin/env bash
# Apply sql/migrations/*.sql to Cloud SQL (or local via DATABASE_URL).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${GCP_PROJECT:-jaybel-dev}"
INSTANCE="${CLOUD_SQL_INSTANCE:-jaybel-sales-db}"
DB_NAME="${DB_NAME:-jaybel_sales_app}"
DB_USER="${DB_USER:-jaybel}"

if [[ -n "${DATABASE_URL:-}" ]]; then
  echo "Applying migrations via DATABASE_URL ..."
  for f in "$ROOT/sql/migrations/"*.sql; do
    echo "  -> $(basename "$f")"
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
  done
  echo "Done."
  exit 0
fi

echo "Using gcloud sql connect (you will be prompted for DB password) ..."
for f in "$ROOT/sql/migrations/"*.sql; do
  echo "  -> $(basename "$f")"
  gcloud sql connect "$INSTANCE" --user="$DB_USER" --database="$DB_NAME" --project="$PROJECT" \
    < "$f"
done
echo "Done."
