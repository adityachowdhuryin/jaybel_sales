"""Retrieve top-k few-shot examples by lexical overlap (Phase A; embeddings later)."""

from __future__ import annotations

from pipeline.models import FewShotExample, TableMeta
from pipeline.registry.keyword_index import tokenize
from pipeline.sql_generation_config import few_shot_config


def select_few_shots(
    table: TableMeta,
    question: str,
    k: int = 2,
    *,
    join_pattern: str | None = None,
) -> list[FewShotExample]:
    q_tokens = set(tokenize(question))
    cfg = few_shot_config()
    intent_tags = [t.lower() for t in (cfg.get("intent_boost_tags") or [])]

    def score(ex: FewShotExample) -> int:
        ex_tokens = set(tokenize(ex.question))
        base = len(q_tokens & ex_tokens)
        ex_q = ex.question.lower()
        for tag in intent_tags:
            if tag in question.lower() and tag in ex_q:
                base += 2
        if join_pattern and ("join" in ex.sql.lower() or "JOIN" in ex.sql):
            base += 1
        if "account_name" in ex.sql and any(
            w in question.lower() for w in ("customer", "account")
        ):
            base += 2
        if "fiscal_quarter" in ex.sql and "fiscal" in question.lower():
            base += 2
        if "PARTITION BY" in ex.sql.upper() and any(
            w in question.lower() for w in ("each", "per", "top")
        ):
            base += 3
        return base

    if not table.few_shot_examples:
        return []

    ranked = sorted(table.few_shot_examples, key=score, reverse=True)
    selected = ranked[:k]

    if join_pattern and k > 1:
        join_example = next(
            (ex for ex in table.few_shot_examples if "JOIN" in ex.sql),
            None,
        )
        if join_example and join_example not in selected:
            selected = [join_example] + [ex for ex in selected if ex != join_example]
            selected = selected[:k]

    return selected
