#!/usr/bin/env bash
# Quick checks before manual UI testing (v1.2 + chart/answer UX).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API="${API_BASE:-http://127.0.0.1:8001}"
UI="${UI_BASE:-http://127.0.0.1:3000}"

fail=0
check() {
  local name="$1" url="$2"
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
  if [[ "$code" == "200" ]]; then
    echo "OK  $name ($code) $url"
  else
    echo "FAIL $name ($code) $url"
    fail=1
  fi
}

echo "=== Stack health ==="
check "API health" "$API/health"
check "Question catalog" "$API/api/question-catalog/categories"
check "Chat UI" "$UI/chat"

if [[ -d "$ROOT/frontend/node_modules/react-markdown" ]]; then
  echo "OK  react-markdown installed"
else
  echo "FAIL react-markdown missing — run: cd frontend && npm install"
  fail=1
fi

if docker ps --format '{{.Names}}' 2>/dev/null | grep -q jaybel_sales_postgres; then
  echo "OK  Postgres container running"
else
  echo "WARN Postgres not running — run: ./scripts/start-phase-c.sh"
fi

echo ""
if [[ $fail -eq 0 ]]; then
  echo "Ready for manual testing: $UI/chat"
  echo "Set Sales rep code in sidebar (e.g. 37) for rep-specific questions."
else
  echo "Fix failures above, then restart API/UI."
  exit 1
fi
