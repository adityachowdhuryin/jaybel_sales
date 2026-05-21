"""Layer 5 — natural language answer + optional chart_spec."""

from __future__ import annotations

import json
import re
from typing import Any

from pipeline.models import AnswerResult, L1Result, QueryResult
from pipeline.vertex_llm import generate_text

L5_SYSTEM = """You are a business analyst summarizing query results.
Rules:
- Only use numbers and facts present in the JSON data.
- Do not speculate or use external knowledge.
- If empty, say no data found and suggest a more specific question.
- Under 150 words unless necessary.
- If a chart helps, end with a line CHART_JSON: then one JSON object
  {chart_type,line|bar|pie, x, y, title} on the next line.
Otherwise omit CHART_JSON.
"""


class AnswerGenerator:
    def generate(
        self,
        question: str,
        l1: L1Result,
        sql: str,
        query_result: QueryResult,
    ) -> AnswerResult:
        data_sample = query_result.rows[:100]
        user = f"""Question: {question}
SQL (reference): {sql}
Rows returned: {query_result.row_count}
Data JSON:
{json.dumps(data_sample, default=str)[:120000]}
"""
        raw = generate_text(L5_SYSTEM, user, temperature=0.2)
        chart_spec = None
        text = raw
        m = re.search(r"CHART_JSON:\s*(\{.*?\})", raw, re.DOTALL)
        if m:
            try:
                chart_spec = json.loads(m.group(1))
                text = raw[: m.start()].strip()
            except json.JSONDecodeError:
                chart_spec = None
        return AnswerResult(text=text, chart_spec=chart_spec)
