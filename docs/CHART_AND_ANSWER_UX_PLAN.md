# Chart & answer UX — implementation status

**Approved:** 2026-05-22  
**Status:** Complete (P0–P5 + completion pass 2026-05-22)

## Delivered

| Feature | Implementation |
|---------|----------------|
| Smart charts | `pipeline/chart_selector.py` — line / bar / horizontal / pie / paired / grouped |
| KPI cards | `MetricCards.tsx` — 1–2 rows; shows with paired Actual vs Target |
| Markdown answers | L5 sections + `_normalize_markdown_sections` fallback |
| UI refresh | Tokens, Inter, Lucide, DataTable zebra, Explore drawer |
| Tests | `test_chart_selector.py`, `test_answer_markdown.py` |

## Chart matrix

| Intent | Rows | Chart |
|--------|------|-------|
| trend | 2+ | line |
| ranking | 2–25 | bar (horizontal if long labels) |
| comparison | 2–25 | bar |
| aggregation | 1 | KPI cards only |
| comparison + actual/target cols | 1 | paired_bar (+ KPI cards) |
| comparison + actual/target cols | 2+ | grouped_bar |
| breakdown / share / mix | 2–8 | pie |
| lookup | any | no chart |

## Redeploy

After `pipeline/` changes:

```bash
./scripts/deploy-sales-agent-engine.sh --agent-engine-id 8991351443894042624
```

Frontend: restart `npm run dev` (no Agent Engine redeploy needed for UI-only changes).
