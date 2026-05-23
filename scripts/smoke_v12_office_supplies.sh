#!/usr/bin/env bash
# v1.2 smoke tests — pipeline CLI (requires ADC + Vertex for L1/L2).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
REP="${SMOKE_REP_CODE:-}"

echo "=== v1.2 Office Supplies smoke (pipeline) ==="

run_q() {
  local label="$1"
  shift
  echo ""
  echo "--- $label ---"
  PYTHONPATH=. .venv/bin/python scripts/run_pipeline_cli.py "$@" 2>&1 | tail -25
}

run_q "Target (6M)" "How far behind are we on our Overall Business Target of \$6M?"
run_q "Run-rate projection" "What are our Projected Monthly Sales compared to our current Sales Month To Date?"
run_q "Closed accounts" "Which accounts have Closed status but still show historical revenue?"
run_q "Embroidery" "List all embroidery or custom printing jobs we processed this week."

if [[ -n "$REP" ]]; then
  run_q "Rep GP FY" "What is my individual Gross Profit contribution for the 2025-2026 financial year?" --sales-rep-code "$REP"
else
  echo ""
  echo "--- Rep GP (skipped: set SMOKE_REP_CODE) ---"
fi

echo ""
echo "=== Done ==="
