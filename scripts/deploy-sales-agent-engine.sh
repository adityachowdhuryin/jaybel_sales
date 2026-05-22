#!/usr/bin/env bash
# Deploy Jaybel Sales Analytics Agent to Vertex AI Agent Engine (ADK).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT_SRC="$ROOT/agent/sales_analytics_agent"
STAGING="$ROOT/agent/_deploy_staging"
ADK="${ADK_BIN:-}"

if [[ -z "$ADK" ]]; then
  if [[ -x "$ROOT/.venv/bin/adk" ]]; then
    ADK="$ROOT/.venv/bin/adk"
  elif [[ -x "$HOME/Desktop/A2A/.venv/bin/adk" ]]; then
    ADK="$HOME/Desktop/A2A/.venv/bin/adk"
  else
    echo "Install ADK: pip install google-adk (or set ADK_BIN to adk executable)" >&2
    exit 1
  fi
fi

PROJECT="${GCP_PROJECT:-jaybel-dev}"
REGION="${GCP_REGION:-us-central1}"
AGENT_ENGINE_ID="${AGENT_ENGINE_ID:-}"
FORCE_NEW="${FORCE_NEW_ENGINE:-0}"

usage() {
  cat <<EOF
Usage: scripts/deploy-sales-agent-engine.sh [options]

  --project ID          (default: jaybel-dev)
  --region ID           (default: us-central1)
  --agent-engine-id ID  update existing engine
  --force-new-engine    create new engine (omit --agent_engine_id)

After deploy, copy the reasoning engine id into:
  agent/AGENT_ENGINE_RESOURCE.env
  backend/.env  -> AGENT_ENGINE_RESOURCE=projects/.../reasoningEngines/<ID>
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --agent-engine-id) AGENT_ENGINE_ID="$2"; shift 2 ;;
    --force-new-engine) FORCE_NEW=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

echo "Staging deploy bundle at $STAGING ..."
rm -rf "$STAGING"
mkdir -p "$STAGING"
cp "$AGENT_SRC/agent.py" "$STAGING/"
cp "$AGENT_SRC/requirements.txt" "$STAGING/"
cp "$AGENT_SRC/.agent_engine_config.json" "$STAGING/"
cp -r "$ROOT/pipeline" "$STAGING/"
cp -r "$ROOT/schema_registry" "$STAGING/"
cp -r "$ROOT/config" "$STAGING/"

cat > "$STAGING/.env" <<EOF
GOOGLE_CLOUD_PROJECT=$PROJECT
GOOGLE_CLOUD_LOCATION=$REGION
EOF

CMD=("$ADK" deploy agent_engine --project "$PROJECT" --region "$REGION"
  --display_name="Sales and analytics agent"
  --trace_to_cloud --otel_to_cloud)
if [[ -n "$AGENT_ENGINE_ID" && "$FORCE_NEW" -eq 0 ]]; then
  CMD+=(--agent_engine_id "$AGENT_ENGINE_ID")
fi
CMD+=("$STAGING")

echo "Running: ${CMD[*]}"
"${CMD[@]}"

echo ""
echo "Deploy finished. Save the Reasoning Engine resource id from the output above."
echo "Example resource: projects/$PROJECT/locations/$REGION/reasoningEngines/<ID>"
