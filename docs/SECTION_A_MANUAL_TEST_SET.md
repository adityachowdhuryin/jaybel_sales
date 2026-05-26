# Section A — Manual UI test set (new questions)

Use this to verify query-understanding improvements **outside** the curated catalog (`Q001–Q097`) and automated guard cases (`G001–G009`).

**App:** http://localhost:3000/chat  
**Docs:** [QUERY_UNDERSTANDING.md](QUERY_UNDERSTANDING.md)

---

## Before you start

1. Agent Engine deployed after Section A (`pipeline/` + `config/query_understanding.yaml`).
2. Local stack up: Postgres, API `:8001`, UI `:3000`.
3. `gcloud auth application-default login` if live BigQuery answers fail.
4. Use a **new chat session** per scenario block when noted (clean history).

### What to look for in the UI

| Signal | Meaning |
|--------|---------|
| **Clarification chips** | `clarification_needed` — pick one to send the next message |
| **Colored guidance banner** | `user_guidance` — read `code` in devtools SSE if unsure |
| **SQL accordion** | Should **not** open for blocked scenarios |
| **Answer markdown** | Should not invent KPIs when row count is 0 |
| **Source line** | Table display name under the status line |

### Rep code setup

| Mode | Sidebar Settings |
|------|------------------|
| **Rep OFF** | Clear `sales_rep_code` |
| **Rep ON** | e.g. `37` or a valid code from your data |

---

## Pass / fail checklist (per turn)

- [ ] Expected UI element appeared (chips / banner / normal answer)
- [ ] No SQL shown when test says “no SQL”
- [ ] SQL + table shown when test says “should query”
- [ ] Follow-up kept same dataset / filters where noted
- [ ] No fabricated numbers on empty results
- [ ] Agent text does not contradict the banner/chips

---

## Block 1 — Vague questions (A2)

Fresh session, rep code optional.

| ID | Turn | Question | Expected |
|----|------|----------|----------|
| **MA-V01** | 1 | `???` | Clarification chips or vague guidance; **no SQL** |
| **MA-V02** | 1 | `sales` | Vague (metric + period missing); **no SQL** |
| **MA-V03** | 1 | `how are we doing` | Vague; **no SQL** |
| **MA-V04** | 1 | `numbers for Jaybel` | Vague or clarification; **no SQL** |
| **MA-V05** | 2 | *(pick chip)* “Total sales for fiscal year 2025-2026” | Normal pipeline; **SQL + answer** |

**Pass:** MA-V05 succeeds after chip; MA-V01–V04 never show SQL.

---

## Block 2 — Ambiguous table routing (A1)

Fresh session.

| ID | Turn | Question | Expected |
|----|------|----------|----------|
| **MA-A01** | 1 | `How did we perform last calendar month?` | Clarification chips (sales vs new business / performance ambiguity) **or** proceeds with one table if confidence high |
| **MA-A02** | 1 | `Show agent performance for last month` | Clarification (rep dimension vs Frazer new business) **or** clear routing |
| **MA-A03** | 1 | `Revenue breakdown last quarter` | Likely `fact_sales_report`; if chips appear, pick **Sales Report** |
| **MA-A04** | 2 | `Use sales transactions (fact_sales_report) for this question.` | **SQL** on sales fact; sensible breakdown |

**Pass:** At least one of MA-A01/A02 shows chips **or** you can document why it proceeded (high confidence). MA-A04 always runs SQL after disambiguation.

---

## Block 3 — Off-topic (A3)

Fresh session.

| ID | Turn | Question | Expected |
|----|------|----------|----------|
| **MA-O01** | 1 | `Who won the 2024 Australian Open?` | `off_topic` or `out_of_dataset` banner; **no SQL** |
| **MA-O02** | 1 | `Write me a Python script to scrape websites` | Off-topic; **no SQL** |
| **MA-O03** | 1 | `What is our company stock price today?` | Out-of-dataset; **no SQL** |
| **MA-O04** | 1 | `Summarize this email thread about the board meeting` | Out-of-dataset; **no SQL** |

**Pass:** All four block SQL; assistant explains Jaybel sales scope only.

---

## Block 4 — Not in BigQuery (A5)

Fresh session.

| ID | Turn | Question | Expected |
|----|------|----------|----------|
| **MA-D01** | 1 | `What is our HubSpot lead conversion rate this quarter?` | `out_of_dataset`; **no SQL** |
| **MA-D02** | 1 | `Show website traffic vs sales by region` | `out_of_dataset`; **no SQL** |
| **MA-D03** | 1 | `Why does Power BI show -$1,695,009 projected Furniture GP variance?` | Guidance: BI forecast not in BQ; offer actuals/targets/run-rate; **no invented BI number** |
| **MA-D04** | 2 | `Show actual Furniture GP for fiscal year 2025-2026` | **SQL** + answer from BigQuery |

**Pass:** MA-D03 blocks or disclaims BI-only metric; MA-D04 is a valid in-scope follow-up.

---

## Block 5 — Rep context required (A6)

### 5a — Rep code **cleared**

Fresh session, **rep OFF**.

| ID | Turn | Question | Expected |
|----|------|----------|----------|
| **MA-R01** | 1 | `What are my sales this calendar month?` | `rep_context_required` banner; **no SQL** |
| **MA-R02** | 1 | `How much GP did I make in fiscal Q2 2025-2026?` | Rep banner; **no SQL** |
| **MA-R03** | 1 | `Closed-won deals I achieved this month for payout` | Rep banner; **no SQL** |
| **MA-R04** | 1 | `Total sales for fiscal year 2025-2026` | **Normal** (not “my”); **SQL** |

### 5b — Rep code **set** (e.g. `37`)

Same questions in a **new** session, **rep ON**.

| ID | Turn | Question | Expected |
|----|------|----------|----------|
| **MA-R05** | 1 | `What are my sales this calendar month?` | **SQL** filtered to rep |
| **MA-R06** | 1 | `My top 5 customers by GP this fiscal year` | **SQL** + answer |

**Pass:** MA-R01–R03 never SQL without rep; MA-R04 always SQL; MA-R05–R06 SQL with rep filter.

---

## Block 6 — Empty results (A4)

Fresh session, rep optional.

| ID | Turn | Question | Expected |
|----|------|----------|----------|
| **MA-E01** | 1 | `Total sales for customer ACCOUNT_DOES_NOT_EXIST_999 in fiscal year 2025-2026` | **SQL runs**, 0 rows, `empty_result` guidance, no fake KPIs |
| **MA-E02** | 1 | `Sales for product main group XYZ_NONEXISTENT in FY 2025-2026` | Same empty pattern |
| **MA-E03** | 1 | `Invoice lines on 2099-01-01` | 0 rows + suggestions to widen period |

**Pass:** Summary says no rows; suggestions mention period/filters; Key figures not invented.

---

## Block 7 — Follow-up context (A7)

Use **one session** per chain; run turn 1 before turn 2.

### Chain 7A — Filter inheritance

| ID | Turn | Question | Expected |
|----|------|----------|----------|
| **MA-F01** | 1 | `Monthly sales by fiscal month for fiscal year 2025-2026` | SQL on `fact_sales_report`; trend/table |
| **MA-F01** | 2 | `Only include Frazer department` | Same table; SQL adds Frazer filter |
| **MA-F01** | 3 | `Same but only Furniture main group` | Still sales fact; adds product filter |

### Chain 7B — Short follow-up phrasing

| ID | Turn | Question | Expected |
|----|------|----------|----------|
| **MA-F02** | 1 | `Top 10 customers by GP in fiscal Q1 2025-2026` | Ranking SQL |
| **MA-F02** | 2 | `Now FRA territory only` (or `filter territory_code FRA`) | Inherits GP + fiscal Q1; uses `territory_code = 'FRA'` — not APAC |
| **MA-F02** | 3 | `Break down by fiscal month` | Trend on same filters |

### Chain 7C — Metric change (explicit)

| ID | Turn | Question | Expected |
|----|------|----------|----------|
| **MA-F03** | 1 | `Total new business revenue FY 2025-2026` | `fact_new_business_frazer` |
| **MA-F03** | 2 | `Switch to Jaybel invoice sales for the same period` | **Different** table (sales fact); user explicitly changed dataset |

### Chain 7D — After clarification

| ID | Turn | Question | Expected |
|----|------|----------|----------|
| **MA-F04** | 1 | `Performance last month` | Clarification chips (if shown) |
| **MA-F04** | 2 | *(chip)* `Use sales transactions...` | SQL on sales |
| **MA-F04** | 3 | `Add breakdown by customer industry` | Follow-up on same table |

**Pass:** MA-F01/F02 keep one fact table unless turn explicitly changes it (MA-F03 turn 2).

---

## Block 8 — Happy path controls (should still work)

Fresh session; confirms guards do not over-block.

| ID | Turn | Question | Expected |
|----|------|----------|----------|
| **MA-H01** | 1 | `Total sales excluding GST for fiscal year 2025-2026` | SQL + headline number |
| **MA-H02** | 1 | `How many working days in the current fiscal month?` | `stg_total_working_days` or subquery pattern |
| **MA-H03** | 1 | `Embroidery jobs this calendar week from line descriptions` | Staging / embroidery routing |
| **MA-H04** | 1 | `Compare actual sales to the $6M business target for FY 2025-2026` | Target archetype + actuals |
| **MA-H05** | 1 | `Run-rate projected month sales based on MTD and working days` | Answer includes run-rate **disclaimer** |

**Pass:** All five return data paths without false off-topic/vague blocks.

---

## Block 9 — Realistic multi-turn conversations

Single session each; simulates real user behavior.

### Conversation 9A — Executive drill-down

1. `Overall business sales vs $6,067,292 target for FY 2025-2026`  
2. `Which product main groups are driving the gap?`  
3. `Show top 5 customers in the worst-performing group`  

**Expected:** Turn 1 target comparison; 2–3 stay on sales fact with deepening filters.

### Conversation 9B — Rep day (rep ON)

1. `My sales this month`  
2. `How does that compare to same month last calendar year?`  
3. `Who are my top 3 accounts by GP?`  

**Expected:** All rep-scoped; no rep banner after turn 1.

### Conversation 9C — Mixed failure recovery

1. `hello` → vague/clarify  
2. `Total GP by territory FY 2025-2026` → normal answer  
3. `What's the weather in Brisbane?` → off-topic; **no SQL**  
4. `Back to GP by territory but only Q2` → sales answer again  

**Expected:** Turn 3 blocked; turn 4 recovers without breaking session.

---

## Block 10 — Edge cases

| ID | Turn | Setup | Question | Expected |
|----|------|-------|----------|----------|
| **MA-X01** | 1 | Rep OFF | `My team's commission for last month` | Rep required |
| **MA-X02** | 1 | Fresh | `Frazer new business and Jaybel sales last month side by side` | May clarify or dual-metric SQL; document behavior |
| **MA-X03** | 1 | After MA-H01 | `Same question but for fiscal 2024-2025` | Period change only; same table |
| **MA-X04** | 1 | Fresh | `LIMIT test` / nonsense `asdfasdf` | Vague or off-topic; no crash |
| **MA-X05** | 1 | Fresh | `GP` | Vague single token; **no SQL** |

---

## Quick scoring sheet

| Block | Tests | Pass | Fail | Notes |
|-------|-------|------|------|-------|
| 1 Vague | 5 | | | |
| 2 Ambiguous | 4 | | | |
| 3 Off-topic | 4 | | | |
| 4 Out-of-dataset | 4 | | | |
| 5 Rep gate | 6 | | | |
| 6 Empty | 3 | | | |
| 7 Follow-ups | 4 chains | | | |
| 8 Happy path | 5 | | | |
| 9 Conversations | 3 | | | |
| 10 Edge | 5 | | | |

**Target:** ≥ 90% pass on blocks 1–7 (core Section A). Blocks 8–9 should be 100%.

---

## Optional: inspect SSE in browser

1. DevTools → Network → `stream` request.  
2. Read `data:` lines for `clarification_needed`, `user_guidance`, `empty_result` in `results`.  
3. Confirm `stop_reason` in final tool payload: `clarification`, `guidance`, or `none`.

---

## Related automated checks

```bash
# Scope guards only (no Vertex)
python scripts/run_qa_suite.py --mode guard --cases G001-G009 --source query_understanding_guards

# Unit tests
python -m unittest tests.test_scope_guard tests.test_routing_decision tests.test_followup_context -v
```

This manual set is **not** wired into `run_qa_suite.py`; it is for human UI validation only.
