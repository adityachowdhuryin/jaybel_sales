"""Vertex AI Agent Engine entrypoint — wraps Phase A pipeline."""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

# Staging deploy: agent.py sits beside pipeline/. Dev: agent/sales_analytics_agent/agent.py
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE if (_HERE / "pipeline").is_dir() else _HERE.parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, ToolContext

from pipeline.pipeline import Pipeline
from pipeline.user_context import UserContext

logger = logging.getLogger(__name__)

SALES_PAYLOAD_PREFIX = "SALES_ANALYTICS_JSON:"
_SALES_CONTEXT_RE = re.compile(
    r"^\[SALES_CONTEXT\]\s*(\{.*?\})\s*\[/SALES_CONTEXT\]\s*\n\n",
    re.DOTALL,
)

_pipeline: Pipeline | None = None


def _parse_sales_context(question: str) -> tuple[str, dict[str, Any]]:
    m = _SALES_CONTEXT_RE.match(question)
    if not m:
        return question, {}
    try:
        ctx = json.loads(m.group(1))
        if not isinstance(ctx, dict):
            ctx = {}
    except json.JSONDecodeError:
        ctx = {}
    return question[m.end() :], ctx


def _get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline()
    return _pipeline


def _to_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _context_from_tool(
    tool_context: ToolContext | None,
    sales_rep_code: str | None = None,
    user_id: str | None = None,
) -> UserContext:
    state: dict[str, Any] = {}
    if tool_context is not None:
        raw = getattr(tool_context, "state", None)
        if isinstance(raw, dict):
            state = raw
    merged = {
        "user_id": user_id or state.get("user_id"),
        "sales_rep_code": sales_rep_code or state.get("sales_rep_code"),
    }
    return UserContext.from_mapping(merged)


def query_sales_analytics(
    question: str,
    sales_rep_code: str = "",
    user_id: str = "",
    history_json: str = "",
    tool_context: ToolContext | None = None,
) -> str:
    """
    Run the full NL-to-SQL pipeline: route, generate SQL, validate, execute BigQuery, summarize.

    Args:
        question: Natural language sales / analytics question.
        sales_rep_code: Optional rep code for "my sales" style questions (from local Postgres user).
        user_id: Optional local app user id (Phase C passes from Postgres).
        history_json: Optional JSON array of prior turns (from [SALES_CONTEXT] or explicit).

    Returns:
        JSON string prefixed with SALES_ANALYTICS_JSON: containing sql, rows, answer, and events.
    """
    clean_question, envelope = _parse_sales_context(question)
    history = envelope.get("history")
    if not isinstance(history, list):
        history = None
    if history_json and not history:
        try:
            parsed = json.loads(history_json)
            if isinstance(parsed, list):
                history = parsed
        except json.JSONDecodeError:
            logger.warning("Invalid history_json on tool call")

    ctx = _context_from_tool(
        tool_context,
        sales_rep_code=sales_rep_code or envelope.get("sales_rep_code") or None,
        user_id=user_id or None,
    )
    try:
        result = _get_pipeline().run(
            clean_question,
            history=history,
            user_context=ctx,
        )
        payload: dict[str, Any] = {
            "query_id": result.query_id,
            "success": not any(e.type == "error" for e in result.events),
            "events": [e.to_dict() for e in result.events],
            "table_id": result.l1.table_id if result.l1 else None,
            "join_pattern": result.l1.join_pattern if result.l1 else None,
            "intent": result.l1.intent if result.l1 else None,
            "sql": result.sql,
            "row_count": result.query_result.row_count if result.query_result else 0,
            "columns": result.query_result.columns if result.query_result else [],
            "rows_sample": result.query_result.rows[:100] if result.query_result else [],
            "answer": result.answer.text if result.answer else None,
            "chart_spec": result.answer.chart_spec if result.answer else None,
        }
        if result.l1:
            payload["l1"] = {
                "table_id": result.l1.table_id,
                "join_pattern": result.l1.join_pattern,
                "confidence": result.l1.confidence,
                "plan": result.l1.plan,
            }
        body = _to_json(payload)
        return f"{SALES_PAYLOAD_PREFIX}{body}"
    except Exception as exc:
        logger.exception("query_sales_analytics failed")
        err = _to_json({"success": False, "error": str(exc)})
        return f"{SALES_PAYLOAD_PREFIX}{err}"


# Aliases matching .agent_engine_config.json tool names (same implementation).
route_and_plan = query_sales_analytics
generate_and_validate_sql = query_sales_analytics
execute_bigquery_sql = query_sales_analytics
summarize_results = query_sales_analytics


root_agent = LlmAgent(
    name="jaybel_sales_analytics_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Jaybel Sales Analytics assistant. All data answers must come from "
        "BigQuery via the query_sales_analytics tool — never invent metrics.\n\n"
        "MANDATORY: Call query_sales_analytics for every question about sales, revenue, "
        "gross profit, customers, products, reps, fiscal periods, working days, or Frazer "
        "new business.\n\n"
        "When the tool returns a string starting with SALES_ANALYTICS_JSON:, parse the JSON "
        "after that prefix. If success is false or events contain type error, explain the "
        "error clearly to the user.\n\n"
        "If success is true: summarize answer and key numbers from the tool payload; mention "
        "which table was queried; you may reference sql briefly. Prefer the answer field when "
        "present. Show a compact markdown table if rows_sample has data. If chart_spec is "
        "present, describe the chart.\n\n"
        "If the user asks about Power BI targets/projections ($6M target, projected GP) and "
        "the data is not in the payload, say those metrics are not in BigQuery yet and report "
        "what you can compute from facts.\n\n"
        "Messages may include a [SALES_CONTEXT]{...}[/SALES_CONTEXT] block with history and "
        "sales_rep_code. Pass the full message string into query_sales_analytics unchanged. "
        "Also pass history_json as a JSON string copy of the history array when present.\n\n"
        "When the client provides sales_rep_code or user_id, pass them into query_sales_analytics "
        "for rep-scoped questions (my sales, my GP).\n\n"
        "Do not expose chain-of-thought. Do not run SQL yourself."
    ),
    tools=[FunctionTool(query_sales_analytics)],
)
