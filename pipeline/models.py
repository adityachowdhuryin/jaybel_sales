"""Shared datatypes for the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ColumnMeta:
    name: str
    type: str
    description: str
    nullable: bool = True
    sample_values: list[Any] = field(default_factory=list)


@dataclass
class FewShotExample:
    question: str
    sql: str


@dataclass
class TableMeta:
    table_id: str
    display_name: str
    layer: str
    agent_default: bool
    routing_priority: str
    description: str
    business_tags: list[str]
    grain: str
    columns: list[ColumnMeta]
    relationships: list[dict[str, str]]
    common_filters: list[str]
    common_aggregations: list[list[str]]
    time_columns: list[str]
    few_shot_examples: list[FewShotExample]

    def column_names(self) -> set[str]:
        return {c.name for c in self.columns}

    def routing_summary(self) -> str:
        tags = ", ".join(self.business_tags[:12])
        return f"{self.table_id} | {self.display_name} | {tags}"


@dataclass
class TimeRange:
    start: str  # ISO date YYYY-MM-DD
    end: str
    label: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"start": self.start, "end": self.end, "label": self.label}


@dataclass
class L1Result:
    intent: str
    table_id: str
    join_pattern: str | None
    confidence: float
    entities: list[str]
    time_range: TimeRange | None
    plan: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> L1Result:
        tr = data.get("time_range")
        time_range = None
        if tr and tr.get("start") and tr.get("end"):
            time_range = TimeRange(
                start=str(tr["start"]),
                end=str(tr["end"]),
                label=str(tr.get("label", "")),
            )
        jp = data.get("join_pattern")
        if jp in (None, "null", ""):
            jp = None
        return cls(
            intent=str(data.get("intent", "aggregation")),
            table_id=str(data["table_id"]),
            join_pattern=jp,
            confidence=float(data.get("confidence", 0.0)),
            entities=list(data.get("entities") or []),
            time_range=time_range,
            plan=list(data.get("plan") or []),
        )


@dataclass
class ValidationResult:
    passed: bool
    validator: str
    message: str = ""
    bytes_scanned: int | None = None


@dataclass
class QueryResult:
    rows: list[dict[str, Any]]
    columns: list[str]
    row_count: int
    empty_result: bool
    bytes_scanned: int | None = None


@dataclass
class AnswerResult:
    text: str
    chart_spec: dict[str, Any] | None = None
