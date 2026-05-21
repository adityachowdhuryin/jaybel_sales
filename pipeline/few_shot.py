"""Retrieve top-k few-shot examples by lexical overlap (Phase A; embeddings later)."""

from __future__ import annotations

from pipeline.models import FewShotExample, TableMeta
from pipeline.registry.keyword_index import tokenize


def select_few_shots(table: TableMeta, question: str, k: int = 2) -> list[FewShotExample]:
    q_tokens = set(tokenize(question))
    if not q_tokens:
        return table.few_shot_examples[:k]

    def score(ex: FewShotExample) -> int:
        ex_tokens = set(tokenize(ex.question))
        return len(q_tokens & ex_tokens)

    ranked = sorted(table.few_shot_examples, key=score, reverse=True)
    return ranked[:k]
