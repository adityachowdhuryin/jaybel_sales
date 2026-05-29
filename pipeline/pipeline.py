"""End-to-end NL-to-SQL pipeline (Phase A + Section A query understanding)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Iterator

from pipeline.answer_generator import AnswerGenerator
from pipeline.chart_selector import select_chart
from pipeline.bq_executor import BQExecutor
from pipeline.empty_result_answer import (
    build_empty_result_markdown,
    empty_result_guidance_suggestions,
)
from pipeline.column_repair import repair_sql_from_validation
from pipeline.events import (
    PipelineEvent,
    chart_spec,
    clarification_needed,
    cost_warning,
    done,
    error,
    results,
    sql_event,
    status,
    table_name,
    token,
    user_guidance,
)
from pipeline.followup_context import FollowUpContext, format_l1_history_block
from pipeline.intent_router import IntentRouter
from pipeline.models import AnswerResult, L1Result, PipelineStopReason, QueryResult, ValidationResult
from pipeline.query_understanding_config import empty_result_config
from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.keyword_index import KeywordIndex
from pipeline.registry.loader import Registry
from pipeline.routing_decision import RoutingDecision
from pipeline.scope_guard import ScopeGuard
from pipeline.sql_generation_config import repair_config
from pipeline.sql_generator import SQLGenerator
from pipeline.sql_repair_hints import friendly_validation_message, structured_repair_hint
from pipeline.user_context import UserContext, normalize_company_possessive
from pipeline.validators.orchestrator import ValidationOrchestrator


@dataclass
class PipelineResult:
    events: list[PipelineEvent] = field(default_factory=list)
    l1: L1Result | None = None
    sql: str | None = None
    query_result: QueryResult | None = None
    answer: AnswerResult | None = None
    query_id: str = ""
    stop_reason: PipelineStopReason = PipelineStopReason.NONE
    guidance_code: str | None = None
    validation_detail: str | None = None


class Pipeline:
    """Runs L1–L5 and yields UI events."""

    def __init__(self, registry: Registry | None = None) -> None:
        self.registry = registry or Registry()
        self.keyword_index = KeywordIndex(self.registry.tables)
        self.allowlist = JoinAllowlist()
        self.router = IntentRouter(self.registry, self.keyword_index, self.allowlist)
        self.scope_guard = ScopeGuard()
        self.routing_decision = RoutingDecision(self.registry)
        self.sql_gen = SQLGenerator(self.registry, self.allowlist)
        self.validator = ValidationOrchestrator(self.registry, self.allowlist)
        self.executor = BQExecutor()
        self.answer_gen = AnswerGenerator()

    def _generate_validated_sql(
        self,
        question: str,
        l1: L1Result,
        ctx: UserContext,
        followup_ctx: FollowUpContext,
    ) -> tuple[str | None, list[ValidationResult], ValidationResult | None]:
        cfg = repair_config()
        max_llm_retries = int(cfg.get("max_llm_retries", 2))
        deterministic_first = bool(cfg.get("deterministic_first", True))

        sql = self.sql_gen.generate(
            question,
            l1,
            user_context=ctx,
            followup_ctx=followup_ctx,
        )
        llm_retries = 0
        validation: list[ValidationResult] = []

        while True:
            validation = self.validator.validate_all(sql)
            if self.validator.all_passed(validation):
                return sql, validation, None

            fail = self.validator.first_failure(validation)
            if not fail:
                return None, validation, None

            if self.validator.safety_failed(validation):
                return None, validation, fail

            if deterministic_first and fail.validator == "column_check":
                repaired, changed = repair_sql_from_validation(
                    sql, fail, table_id=l1.table_id
                )
                if changed:
                    sql = repaired
                    continue

            if llm_retries >= max_llm_retries:
                return None, validation, fail

            hint = structured_repair_hint(fail)
            sql = self.sql_gen.generate(
                question,
                l1,
                repair_hint=hint,
                user_context=ctx,
                followup_ctx=followup_ctx,
            )
            llm_retries += 1

    def run(
        self,
        question: str,
        *,
        session_id: str | None = None,
        history: list[dict[str, Any]] | None = None,
        user_context: UserContext | dict[str, Any] | None = None,
        skip_execute: bool = False,
    ) -> PipelineResult:
        query_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        ctx = (
            user_context
            if isinstance(user_context, UserContext)
            else UserContext.from_mapping(user_context)
        )
        out = PipelineResult(query_id=query_id)
        events: list[PipelineEvent] = []
        question = normalize_company_possessive(question)
        followup_ctx = FollowUpContext.from_history(history, question)

        def emit(e: PipelineEvent) -> None:
            events.append(e)

        def emit_tokens_from_text(text: str, *, single_chunk: bool = False) -> None:
            if single_chunk:
                emit(token(text))
                return
            for word in text.split():
                emit(token(word + " "))

        def finish_stop(
            reason: PipelineStopReason,
            *,
            guidance_code: str | None = None,
            answer_text: str | None = None,
        ) -> PipelineResult:
            out.stop_reason = reason
            out.guidance_code = guidance_code
            if answer_text:
                out.answer = AnswerResult(text=answer_text)
                emit_tokens_from_text(answer_text)
            emit(done(session_id, query_id))
            out.events = events
            return out

        try:
            emit(status("Analyzing your question..."))

            scope = self.scope_guard.evaluate(
                question,
                ctx,
                history,
                is_follow_up=followup_ctx.is_follow_up,
            )
            if scope.blocked:
                if scope.clarification:
                    c = scope.clarification
                    emit(
                        clarification_needed(
                            c.code,
                            c.message,
                            [o.to_dict() for o in c.options],
                        )
                    )
                    return finish_stop(
                        PipelineStopReason.CLARIFICATION,
                        guidance_code=scope.reason_code,
                        answer_text=c.message,
                    )
                emit(
                    user_guidance(
                        scope.reason_code or "guidance",
                        scope.message,
                        scope.suggestions or None,
                    )
                )
                return finish_stop(
                    PipelineStopReason.GUIDANCE,
                    guidance_code=scope.reason_code,
                    answer_text=scope.message,
                )

            hist_block = format_l1_history_block(history, followup_ctx)
            l1 = self.router.route(
                question,
                history=history,
                user_context=ctx,
                history_block=hist_block,
            )
            out.l1 = l1
            followup_ctx.apply_to_l1(l1, set(self.registry.tables.keys()))

            keyword_ranked = self.keyword_index.lookup(question, top_k=3)
            routing = self.routing_decision.evaluate(
                l1,
                keyword_ranked,
                question,
                is_follow_up=followup_ctx.is_follow_up,
            )
            if not routing.proceed and routing.clarification:
                c = routing.clarification
                emit(
                    table_name(
                        l1.table_id,
                        self.router.display_name(l1.table_id),
                    )
                )
                emit(
                    clarification_needed(
                        c.code,
                        c.message,
                        [o.to_dict() for o in c.options],
                    )
                )
                return finish_stop(
                    PipelineStopReason.CLARIFICATION,
                    guidance_code=c.code,
                    answer_text=c.message,
                )

            emit(
                table_name(
                    l1.table_id,
                    self.router.display_name(l1.table_id),
                )
            )

            emit(status("Generating query..."))
            sql, validation, fail = self._generate_validated_sql(
                question, l1, ctx, followup_ctx
            )
            if sql is None:
                fail = fail or self.validator.first_failure(validation)
                friendly_msg, suggestions = friendly_validation_message(fail) if fail else (
                    "The query could not be validated.",
                    ["Rephrase your question with a clear metric and time period."],
                )
                technical = fail.message if fail else "SQL validation failed"
                out.validation_detail = technical
                emit(
                    user_guidance(
                        "sql_validation_failed",
                        friendly_msg,
                        suggestions,
                        validation_detail=technical,
                    )
                )
                return finish_stop(
                    PipelineStopReason.GUIDANCE,
                    guidance_code="sql_validation_failed",
                    answer_text=friendly_msg,
                )

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
            emit(
                results(
                    qr.rows,
                    qr.row_count,
                    qr.columns,
                    empty_result=qr.empty_result,
                )
            )

            display = self.router.display_name(l1.table_id)
            if qr.empty_result and not empty_result_config().get("use_llm_for_empty", False):
                emit(status("Summarizing results..."))
                md = build_empty_result_markdown(question, l1, sql, qr, display)
                emit(
                    user_guidance(
                        "empty_result",
                        "No rows matched your filters.",
                        empty_result_guidance_suggestions(l1),
                    )
                )
                out.answer = AnswerResult(text=md, chart_spec=None)
                emit_tokens_from_text(md, single_chunk=True)
            else:
                emit(status("Summarizing results..."))
                answer = self.answer_gen.generate(question, l1, sql, qr)
                if qr.empty_result:
                    emit(
                        user_guidance(
                            "empty_result",
                            "No rows matched your filters.",
                            empty_result_guidance_suggestions(l1),
                        )
                    )
                spec = select_chart(question, l1, qr)
                if spec:
                    answer.chart_spec = spec
                out.answer = answer
                emit_tokens_from_text(answer.text, single_chunk=True)
                if answer.chart_spec:
                    emit(chart_spec(answer.chart_spec))

            emit(done(session_id, query_id))
        except Exception as exc:
            emit(error("pipeline_error", str(exc)))
            out.stop_reason = PipelineStopReason.ERROR

        out.events = events
        return out

    def stream_events(
        self,
        question: str,
        **kwargs: Any,
    ) -> Iterator[PipelineEvent]:
        result = self.run(question, **kwargs)
        yield from result.events
