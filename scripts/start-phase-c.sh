#!/usr/bin/env bash
# Start Phase C stack (Postgres + API + UI hints)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Starting Postgres (host port 15433)..."
docker-compose up -d postgres

export DATABASE_URL="${DATABASE_URL:-postgresql://jaybel:jaybel_local_dev@localhost:15433/jaybel_sales_app}"
docker-compose exec -T postgres psql -U jaybel -d jaybel_sales_app \
  -f - < sql/migrations/001_initial.sql >/dev/null 2>&1 || true
docker-compose exec -T postgres psql -U jaybel -d jaybel_sales_app \
  -f - < sql/migrations/002_agent_engine_session.sql >/dev/null 2>&1 || true
docker-compose exec -T postgres psql -U jaybel -d jaybel_sales_app \
  -f - < sql/migrations/003_session_ui_context.sql >/dev/null 2>&1 || true
docker-compose exec -T postgres psql -U jaybel -d jaybel_sales_app \
  -f - < sql/migrations/004_turn_feedback.sql >/dev/null 2>&1 || true

if [[ ! -f backend/.env ]]; then
  cp backend/.env.example backend/.env
fi

echo ""
echo "API:  PYTHONPATH=. .venv/bin/uvicorn backend.main:app --reload --port 8000"
echo "UI:   cd frontend && npm run dev"
echo ""
echo "Open http://localhost:3000/chat"
echo "Note: if port 8000 is in use, use --port 8001 and set NEXT_PUBLIC_API_BASE_URL=http://localhost:8001"
