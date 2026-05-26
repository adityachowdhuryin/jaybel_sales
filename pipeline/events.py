"""UI event types (Agent Engine stream payloads)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PipelineEvent:
    type: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, **self.payload}


def status(message: str) -> PipelineEvent:
    return PipelineEvent("status", {"message": message})


def table_name(table_id: str, display: str) -> PipelineEvent:
    return PipelineEvent("table_name", {"table": table_id, "display": display})


def sql_event(sql: str) -> PipelineEvent:
    return PipelineEvent("sql", {"sql": sql})


def cost_warning(bytes_scanned: int) -> PipelineEvent:
    return PipelineEvent("cost_warning", {"bytes_scanned": bytes_scanned})


def results(
    rows: list[dict],
    row_count: int,
    columns: list[str],
    *,
    empty_result: bool = False,
) -> PipelineEvent:
    return PipelineEvent(
        "results",
        {
            "rows": rows,
            "row_count": row_count,
            "columns": columns,
            "empty_result": empty_result,
        },
    )


def clarification_needed(
    code: str,
    message: str,
    options: list[dict[str, str]],
) -> PipelineEvent:
    return PipelineEvent(
        "clarification_needed",
        {"code": code, "message": message, "options": options},
    )


def user_guidance(
    code: str,
    message: str,
    suggestions: list[str] | None = None,
    validation_detail: str | None = None,
) -> PipelineEvent:
    payload: dict[str, Any] = {"code": code, "message": message}
    if suggestions:
        payload["suggestions"] = suggestions
    if validation_detail:
        payload["validation_detail"] = validation_detail
    return PipelineEvent("user_guidance", payload)


def token(text: str) -> PipelineEvent:
    return PipelineEvent("token", {"text": text})


def chart_spec(spec: dict[str, Any]) -> PipelineEvent:
    return PipelineEvent("chart_spec", spec)


def done(session_id: str, query_id: str) -> PipelineEvent:
    return PipelineEvent("done", {"session_id": session_id, "query_id": query_id})


def error(code: str, message: str) -> PipelineEvent:
    return PipelineEvent("error", {"code": code, "message": message})
