#!/usr/bin/env bash
# One-shot prep before UI testing (Section A + SQL hardening).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-8001}"
export API_BASE="http://127.0.0.1:${API_PORT}"

echo "=== 1/7 Section A unit + guard tests ==="
.venv/bin/python -m unittest \
  tests.test_rep_gate \
  tests.test_scope_guard \
  tests.test_routing_decision \
  tests.test_followup_context \
  tests.test_empty_result_answer \
  -q
.venv/bin/python scripts/run_qa_suite.py --mode guard --cases G001-G009

echo ""
echo "=== 2/7 SQL hardening unit tests ==="
.venv/bin/python -m pytest \
  tests/test_schema_context.py \
  tests/test_column_repair.py \
  tests/test_followup_sql_context.py \
  tests/test_sql_column_typos.py \
  -q

if [[ "${RUN_SQL_REGRESSION:-0}" == "1" ]]; then
  echo ""
  echo "=== Optional SQL regression (Vertex, ~2 min) ==="
  .venv/bin/python scripts/run_qa_suite.py --mode sql_regression --cases S001-S012
else
  echo ""
  echo "=== SQL regression skipped (set RUN_SQL_REGRESSION=1 to run S001-S012) ==="
fi

echo ""
echo "=== 3/7 Docker / Postgres ==="
if ! docker info >/dev/null 2>&1; then
  if command -v colima >/dev/null 2>&1; then
    echo "Starting Colima..."
    colima start
  else
    echo "ERROR: Docker not running. Start Docker Desktop or Colima." >&2
    exit 1
  fi
fi
./scripts/start-phase-c.sh

echo ""
echo "=== 4/7 Env files ==="
[[ -f backend/.env ]] || cp backend/.env.example backend/.env
[[ -f frontend/.env.local ]] || cp frontend/.env.local.example frontend/.env.local
if grep -q '^API_PORT=' backend/.env 2>/dev/null; then
  sed -i '' "s/^API_PORT=.*/API_PORT=${API_PORT}/" backend/.env 2>/dev/null || \
    sed -i "s/^API_PORT=.*/API_PORT=${API_PORT}/" backend/.env
else
  echo "API_PORT=${API_PORT}" >> backend/.env
fi
if ! grep -q "localhost:${API_PORT}" frontend/.env.local 2>/dev/null; then
  if grep -q '^NEXT_PUBLIC_API_BASE_URL=' frontend/.env.local; then
    sed -i '' "s|^NEXT_PUBLIC_API_BASE_URL=.*|NEXT_PUBLIC_API_BASE_URL=http://localhost:${API_PORT}|" frontend/.env.local 2>/dev/null || \
      sed -i "s|^NEXT_PUBLIC_API_BASE_URL=.*|NEXT_PUBLIC_API_BASE_URL=http://localhost:${API_PORT}|" frontend/.env.local
  else
    echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:${API_PORT}" >> frontend/.env.local
  fi
fi

echo ""
echo "=== 5/7 Python + Node deps ==="
.venv/bin/pip install -q -r backend/requirements.txt 2>/dev/null || true
(cd frontend && npm install --silent)

echo ""
echo "=== 6/7 Agent Engine deploy ==="
if [[ "${SKIP_AGENT_DEPLOY:-0}" == "1" ]]; then
  echo "SKIP_AGENT_DEPLOY=1 — skipping deploy (engine 8991351443894042624)"
else
  ./scripts/deploy-sales-agent-engine.sh --agent-engine-id "${AGENT_ENGINE_ID:-8991351443894042624}"
fi

echo ""
echo "=== 7/7 GCP auth + stack health ==="
if gcloud auth application-default print-access-token >/dev/null 2>&1; then
  echo "OK  application-default credentials"
else
  echo "WARN Run: gcloud auth application-default login"
fi

if curl -sf "${API_BASE}/health" >/dev/null 2>&1; then
  echo "OK  API already running at ${API_BASE}"
  API_BASE="${API_BASE}" ./scripts/test_improvements_ui.sh || true
else
  echo "WARN API not running — start with:"
  echo "  PYTHONPATH=. .venv/bin/uvicorn backend.main:app --reload --host 127.0.0.1 --port ${API_PORT}"
fi

echo ""
echo "=============================================="
echo "Ready for UI testing"
echo "  Open:  http://localhost:3000/chat"
echo "  Guide: docs/UI_TEST_READY.md"
echo "  Tests: docs/SECTION_A_MANUAL_TEST_SET.md"
echo "=============================================="
