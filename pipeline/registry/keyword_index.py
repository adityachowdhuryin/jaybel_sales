"""Inverted keyword index for zero-cost table routing hints."""

from __future__ import annotations

import re
from collections import defaultdict

from pipeline.models import TableMeta

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class KeywordIndex:
    def __init__(self, tables: dict[str, TableMeta]) -> None:
        self._index: dict[str, set[str]] = defaultdict(set)
        self._build(tables)

    def _build(self, tables: dict[str, TableMeta]) -> None:
        for table_id, meta in tables.items():
            sources = [
                meta.display_name,
                meta.description,
                meta.grain,
                " ".join(meta.business_tags),
                " ".join(c.description for c in meta.columns),
                " ".join(c.name.replace("_", " ") for c in meta.columns),
            ]
            for text in sources:
                for token in tokenize(text):
                    if len(token) >= 2:
                        self._index[token].add(table_id)
            # Short table name token e.g. fact_sales_report
            short = table_id.split(".")[-1]
            for token in tokenize(short.replace("_", " ")):
                self._index[token].add(table_id)

    def lookup(self, question: str, top_k: int = 2) -> list[tuple[str, int]]:
        scores: dict[str, int] = defaultdict(int)
        for token in tokenize(question):
            for table_id in self._index.get(token, ()):
                scores[table_id] += 1
        ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        return ranked[:top_k]

    def top_table_ids(self, question: str, top_k: int = 2) -> list[str]:
        return [tid for tid, _ in self.lookup(question, top_k=top_k)]
