# Query understanding (Section A)

Pre-SQL gates and clarification for the Jaybel NL→SQL pipeline.

## Flow

1. **ScopeGuard** — rep code, vague, off-topic, out-of-dataset (before L1)
2. **IntentRouter (L1)** — table, intent, confidence
3. **FollowUpContext** — inherit prior table for short follow-ups
4. **RoutingDecision** — keyword vs L1 fan-in; clarification if low confidence
5. **L2–L5** — SQL, BigQuery, answer (or empty-result template)

## SSE events

| Event | When |
|-------|------|
| `clarification_needed` | Ambiguous table or vague question (options for chips) |
| `user_guidance` | `rep_context_required`, `off_topic`, `out_of_dataset`, `empty_result` |

Both are **success** paths (`success: true` in tool payload), not errors.

## Configuration

[`config/query_understanding.yaml`](../config/query_understanding.yaml) — thresholds, keywords, rep patterns.

## Deploy

After changing `pipeline/` or config, redeploy Agent Engine:

```bash
./scripts/deploy-sales-agent-engine.sh
```

## QA

Guard cases `G001–G009` in [`docs/qa_evaluation_set.yaml`](qa_evaluation_set.yaml):

```bash
python scripts/run_qa_suite.py --mode guard --cases G001-G009 --source query_understanding_guards
```

## Manual UI test set (full)

For thorough validation with follow-up chains (outside Q001–Q097), see **[SECTION_A_MANUAL_TEST_SET.md](SECTION_A_MANUAL_TEST_SET.md)** (~40 scenarios, blocks 1–10).

## Manual smoke (quick)

| Question | Expected |
|----------|----------|
| "What is the capital of France?" | `out_of_dataset` guidance, no SQL |
| "my sales this month" (no rep code) | **SQL** company-wide ("my" → "our") |
| "my commission this quarter" (no rep code) | `rep_context_required` |
| "total sales this year" | FY filter (`dim_date.fy`), not calendar Jan–Dec |
| "help" | Vague clarification chips |
| "show performance last month" | Table clarification chips (if L1/keyword disagree) |
| Follow-up after a prior answer | Same table as prior turn |
