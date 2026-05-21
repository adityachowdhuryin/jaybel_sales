"""End-to-end NL-to-SQL pipeline (Phase A)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Iterator

from pipeline.answer_generator import AnswerGenerator
from pipeline.bq_executor import BQExecutor
from pipeline.events import (
    PipelineEvent,
    chart_spec,
    cost_warning,
    done,
    error,
    results,
    sql_event,
    status,
    table_name,
    token,
)
from pipeline.intent_router import IntentRouter
from pipeline.models import AnswerResult, L1Result, QueryResult
from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.keyword_index import KeywordIndex
from pipeline.registry.loader import Registry
from pipeline.sql_generator import SQLGenerator
from pipeline.validators.orchestrator import ValidationOrchestrator


@dataclass
class PipelineResult:
    events: list[PipelineEvent] = field(default_factory=list)
    l1: L1Result | None = None
    sql: str | None = None
    query_result: QueryResult | None = None
    answer: AnswerResult | None = None
    query_id: str = ""


class Pipeline:
    """Runs L1–L5 and yields UI events."""

    def __init__(self, registry: Registry | None = None) -> None:
        self.registry = registry or Registry()
        self.keyword_index = KeywordIndex(self.registry.tables)
        self.allowlist = JoinAllowlist()
        self.router = IntentRouter(self.registry, self.keyword_index, self.allowlist)
        self.sql_gen = SQLGenerator(self.registry, self.allowlist)
        self.validator = ValidationOrchestrator(self.registry, self.allowlist)
        self.executor = BQExecutor()
        self.answer_gen = AnswerGenerator()

    def run(
        self,
        question: str,
        *,
        session_id: str | None = None,
        history: list[dict[str, Any]] | None = None,
        skip_execute: bool = False,
    ) -> PipelineResult:
        query_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        out = PipelineResult(query_id=query_id)
        events: list[PipelineEvent] = []

        def emit(e: PipelineEvent) -> None:
            events.append(e)

        try:
            emit(status("Analyzing your question..."))
            l1 = self.router.route(question, history=history)
            out.l1 = l1
            emit(
                table_name(
                    l1.table_id,
                    self.router.display_name(l1.table_id),
                )
            )

            emit(status("Generating query..."))
            sql = self.sql_gen.generate(question, l1)
            validation = self.validator.validate_all(sql)
            if not self.validator.all_passed(validation):
                fail = self.validator.first_failure(validation)
                if fail and not self.validator.safety_failed(validation):
                    hint = f"{fail.validator}: {fail.message}"
                    sql = self.sql_gen.generate(question, l1, repair_hint=hint)
                    validation = self.validator.validate_all(sql)
                if not self.validator.all_passed(validation):
                    fail = self.validator.first_failure(validation)
                    emit(
                        error(
                            "validation_failed",
                            fail.message if fail else "SQL validation failed",
                        )
                    )
                    out.events = events
                    return out

            out.sql = sql
            emit(sql_event(sql))

            for v in validation:
                if v.validator == "dry_run" and v.bytes_scanned:
                    from pipeline.config import bytes_scanned_limit_gb

                    if v.bytes_scanned > int(bytes_scanned_limit_gb() * 1e9):
                        emit(cost_warning(v.bytes_scanned))

            if skip_execute:
                emit(done(session_id, query_id))
                out.events = events
                return out

            emit(status("Running query..."))
            qr = self.executor.run(sql)
            out.query_result = qr
            emit(results(qr.rows, qr.row_count, qr.columns))

            emit(status("Summarizing results..."))
            answer = self.answer_gen.generate(question, l1, sql, qr)
            out.answer = answer
            for word in answer.text.split():
                emit(token(word + " "))
            if answer.chart_spec:
                emit(chart_spec(answer.chart_spec))

            emit(done(session_id, query_id))
        except Exception as exc:
            emit(error("pipeline_error", str(exc)))

        out.events = events
        return out

    def stream_events(
        self,
        question: str,
        **kwargs: Any,
    ) -> Iterator[PipelineEvent]:
        result = self.run(question, **kwargs)
        yield from result.events
