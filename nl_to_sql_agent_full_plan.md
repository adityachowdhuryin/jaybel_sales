# NL-to-SQL Sales & Analytics Agent — Complete Implementation Plan

## Jaybel environment (configured — ready for implementation)

| Setting | Value |
|---------|--------|
| GCP project | `jaybel-dev` |
| Region | `us-central1` (Iowa) |
| BigQuery dataset | `jaybel_sales_analytics` |
| Tables | 13 (6 staging, 5 dimensions, 2 facts) — see `schema_registry/tables/` |
| Runtime SA (initial) | `115724636423-compute@developer.gserviceaccount.com` |
| Owner / IAM | `aditya.chowdhury@giantleapsystems.com` |
| UI entry | **Vertex AI Agent Engine only** (every chat = Agent Engine invocation / telemetry) |
| Policy | None for v1 (10GB dry-run soft warning in `config/jaybel.yaml`) |
| Fiscal year | July=FM1 … June=FM12; label `2025-2026` |
| Relative dates | **`Australia/Sydney`**; default = **calendar** month/quarter (use **fiscal** only when user says so) |
| Auth (v1) | **Local Postgres user** — no Firebase (`dev@localhost` default) |
| App data storage | **PostgreSQL on local device** — sessions & chat turns (not Firestore) |
| UI hosting (v1) | **localhost** — Next.js `:3000` + FastAPI `:8000` on this machine |
| Analytics data | **BigQuery** in GCP (unchanged — not copied to Postgres) |

**Prepared artifacts (do not re-derive at implementation time):**

| Artifact | Path |
|----------|------|
| GCP config | `config/jaybel.yaml` |
| Table schemas + few-shot SQL | `schema_registry/tables/*.yaml` (13 files) |
| Join allowlist | `schema_registry/join_allowlist.yaml` |
| Business glossary | `docs/business_glossary.md` |
| QA set (97 cases: Q001–Q060 + client Q061–Q097) | `docs/qa_evaluation_set.yaml` (all cases have `category`) |
| UI question catalog (starters + follow-ups) | `content/question_catalog.yaml` — build: `scripts/build_question_catalog.py` |
| Question discovery UI spec | `docs/UI_QUESTION_DISCOVERY_PLAN.md` |
| Client question catalog (source PDF) | `docs/office_supplies_client_questions.md` |
| Client questions PDF | `Office_Supplies_BI_Analytics_Questions.pdf` |
| Agent Engine architecture | `docs/AGENT_ENGINE_ARCHITECTURE.md` |
| Pre-flight checklist | `docs/PRE_IMPLEMENTATION_CHECKLIST.md` |
| Locked decisions | `docs/DECISIONS.md` |
| **Local stack (corrected)** | `docs/ARCHITECTURE_LOCAL.md` |
| Phase C guide | `docs/PHASE_C_LOCAL.md` |
| Postgres migrations | `sql/migrations/001`–`004` (sessions, AE session id, `ui_context`, turn feedback) |
| Agent deploy template | `agent/.agent_engine_config.json` |
| BQ validation report | `docs/bq_schema_validation_report.md` |
| Source PDF | `Jaybel_Sales_Analytics_Detailed_Schema.pdf` |

**v1 routing strategy:** `approved_join_graph` — primary subjects are `fact_sales_report` and `fact_new_business_frazer` with optional joins to all five `dim_*` tables per `join_allowlist.yaml`. Staging tables are used only for raw/source questions or `stg_total_working_days` for working-day KPIs.

**Pre-build sign-off:** See `docs/FINAL_READINESS_REVIEW.md` (plan corrected for Agent Engine streaming vs FastAPI SSE; v1 scope trimmed).

### Jaybel v1 scope (in) vs deferred (out)

| In v1 | Deferred (v1.1+) |
|-------|---------------------|
| Agent Engine + in-process tools (L1–L5) | Redis / Memorystore cache |
| Next.js localhost + **FastAPI localhost** | PDF reports, GCS |
| **PostgreSQL** sessions & turns on local device | Firebase / Firestore |
| Registry, validators, BQ read-only (cloud) | Vertex Memory Bank |
| UI SSE via **local API** → Agent Engine stream | Cloud Run / cloud hosting |
| Question discovery UI (categories, starters, follow-ups) | LLM follow-ups, ⌘K palette, mobile sheet (UI-4) |
| Honest handling of missing target/projection metrics | `pipeline_logs` table |

---

## Project Overview

A production-grade, latency-optimized Natural Language to SQL agent deployed on GCP **Vertex AI Agent Engine**.
Users interact via a Claude-style chatbot UI. They ask questions in plain English.
The agent routes to the correct BigQuery table, generates valid SQL, executes it,
streams a natural language answer back, and optionally renders charts or downloadable reports.

**Core constraints:**
- Minimize hallucination (every validation step is mandatory, never skipped; UI privileges tabular results over narrative)
- Perceived latency to first visible output: under 1.5 seconds (ambitious; see latency note below)
- All LLM inference: Vertex AI (gemini-2.5-flash or successor; pin a stable model ID per environment)
- All data: Google BigQuery
- Frontend: Next.js 14 — **queries only Agent Engine API** (no direct pipeline on Cloud Run)
- Backend: **FastAPI on localhost:8000** (Postgres sessions + chat SSE proxy) + Agent Engine tools on GCP for analytics queries
- Memory: Vertex AI Agent Builder memory / Memory Bank (product name and API surface vary by release; confirm in target GCP region)
- Communication protocol: **Structured streaming events** to the UI (same event types as SSE below), delivered via **Vertex AI Agent Engine** streaming in v1 — not a separate FastAPI SSE hot path

### Vertex AI Agent Engine (locked — Jaybel)

**Decision:** Agent Engine–only entry. See `docs/AGENT_ENGINE_ARCHITECTURE.md`.

1. **Next.js UI** calls **local FastAPI** `POST /api/chat/stream`, which calls Agent Engine `stream_query` for every user message.
2. **Agent Engine** records each interaction in the Agent Engine dashboard (invocation telemetry).
3. **Agent tools** (deployed with the agent) implement L1–L5 in-process: registry, routing, SQL generation, sqlglot + dry run, BigQuery execute, summarization.
4. **FastAPI (localhost:8000)** is **on the hot path for the UI** — persists sessions/turns to **local PostgreSQL** and proxies Agent Engine streaming to the browser. It does **not** replace Agent Engine for analytics queries.

Cloud Run tool callbacks are **not** used in v1 (avoids split telemetry). Revisit only if tool isolation is required later.

### Multi-table questions and JOINs (important gap)

The document largely assumes **one selected `table_id` per question**. Real sales analytics often needs **joins across fact and dimension tables** (e.g. orders + customers + products).

**Jaybel v1 choice:** **Approved join graph** — implemented in `schema_registry/join_allowlist.yaml` (`fact_sales_with_dims`, `fact_new_business_with_dims`). L1 returns `primary_table` + `join_pattern`; L2 must only use joins listed there.

Validator A (column existence) and Validator C (table allowlist) **must be extended** to validate **every table reference** in the SQL when joins are enabled.

---

## Repository Structure

```
project-root/
├── config/
│   └── jaybel.yaml                      # GCP project, dataset, fiscal rules, SA
├── agent/
│   ├── .agent_engine_config.json        # Deploy display name, SA, tool list
│   └── (agent package — implementation phase)
├── schema_registry/
│   ├── join_allowlist.yaml
│   ├── tables/                          # 13 Jaybel BQ tables (generated + curated)
│   │   ├── fact_sales_report.yaml
│   │   ├── fact_new_business_frazer.yaml
│   │   ├── dim_*.yaml
│   │   └── stg_*.yaml
├── docs/
│   ├── business_glossary.md
│   ├── qa_evaluation_set.yaml
│   ├── AGENT_ENGINE_ARCHITECTURE.md
│   └── PRE_IMPLEMENTATION_CHECKLIST.md
├── scripts/
│   └── generate_schema_registry.py
├── content/
│   └── question_catalog.yaml            # UI categories, 97 starters, follow-ups, rules
├── backend/                             # FastAPI localhost:8000
│   ├── main.py
│   ├── routers/                         # sessions, chat, question_catalog
│   ├── services/                        # agent_engine, question_catalog
│   └── db/postgres.py
├── pipeline/                            # L1–L5 (also bundled in Agent Engine deploy)
├── sql/migrations/                      # 001–004 local Postgres
├── docker-compose.yml                   # Postgres host port 15433
├── scripts/
│   ├── build_question_catalog.py
│   ├── deploy-sales-agent-engine.sh
│   └── start-phase-c.sh
├── agent/sales_analytics_agent/         # Agent Engine entry (agent.py)
├── frontend/
│   ├── app/
│   │   ├── page.tsx                     # Root: redirects to /chat
│   │   ├── chat/
│   │   │   └── page.tsx                 # Main chat page
│   │   └── api/
│   │       └── proxy/route.ts           # Optional: proxy SSE to avoid CORS
│   ├── components/
│   │   ├── chat/                        # ChatShell, SessionSidebar, ChatWindow, …
│   │   └── explore/                     # ExploreDrawer, CategoryGrid, StarterList, badges
│   ├── hooks/
│   │   ├── useChatStream.ts
│   │   ├── useQuestionCatalog.ts
│   │   └── useFollowUps.ts
│   ├── lib/
│   │   ├── api.ts
│   │   ├── questionCatalog.ts
│   │   └── sse.ts
│   │   └── reportExport.ts             # CSV + PDF download utilities
│   └── types/
│       └── index.ts                     # All shared TypeScript types
├── infra/
│   ├── gcs_lifecycle.json               # Report bucket lifecycle (auto-delete after 7d) — deferred
│   └── iam_bindings.sh                  # Service account IAM setup script
└── schema_registry_docs/
    └── how_to_add_a_table.md            # Runbook for adding new BQ tables
```

---

## Layer 0 — Schema Registry

### Purpose
The schema registry is the single source of truth for every BigQuery table the agent
can query. It eliminates runtime I/O for schema lookup and is the foundation that
prevents column and table hallucination. Nothing in the pipeline works correctly
without this layer being complete and accurate.

### Structure of Each Table YAML

Each BigQuery table gets one YAML file. Every field is mandatory.

```
table_id: fully-qualified BQ table name (project.dataset.table)
display_name: human-readable name for UI display
description: 2-3 sentence description of what this table contains, 
             its grain, and typical use cases
business_tags: list of keywords users might say that relate to this table
grain: exactly one sentence describing what one row represents
columns:
  - name: exact column name as it appears in BigQuery
    type: BigQuery data type (STRING, INT64, FLOAT64, TIMESTAMP, DATE, BOOL, ARRAY, STRUCT)
    description: what this column means in business terms
    sample_values: list of 3-5 representative values (critical for enum/categorical columns)
    nullable: true or false
relationships:
  - column: local column name
    references: other_table.column (for join awareness)
common_filters: list of columns most commonly used in WHERE clauses
common_aggregations: list of (column, aggregation_function) pairs most common for this table
time_columns: list of columns that represent time (used for time-range filter injection)
few_shot_examples:
  - question: natural language question a user might ask
    sql: the correct BigQuery Standard SQL for that question
  (minimum 8 examples per table, covering: aggregation, trend, comparison, 
   lookup, ranking, filter combinations, date math, and a join if applicable)
```

### Registry Loader Behavior

The registry loader runs once at **agent (or optional FastAPI) startup** (lifespan / init hook).

It performs the following in sequence:

1. Scans the `schema_registry/tables/` directory and loads every YAML file into a
   Python dictionary keyed by `table_id`.

2. Builds an inverted keyword index: for every word in `business_tags`, `description`,
   and all `column.description` fields, it maps the word to the list of table IDs that
   contain it. This powers instant keyword-based table candidate lookup with zero LLM cost.

3. Calls the Vertex AI **text embedding** API once per table with a configurable model ID (e.g. `text-embedding-004` or the current default in your project), using the
   concatenation of: `display_name + description + business_tags + column names + column descriptions`.
   Stores the resulting embedding vector alongside the table metadata. This is done once
   at startup and cached in memory. It is never re-computed per request.

4. For each table's `few_shot_examples`, calls the Vertex AI embedding API on each
   example's `question` field. Stores all example embeddings in a numpy matrix, with
   a parallel list of (question, sql) tuples. This powers fast nearest-neighbor
   few-shot retrieval at query time.

5. Exposes the loaded registry, keyword index, table embedding matrix, and few-shot
   embedding matrix as module-level singletons accessible to the rest of the pipeline.

### Adding a New Table

When a new BigQuery table needs to be queryable:
1. Create a new YAML file in `schema_registry/tables/`
2. Restart the FastAPI server (or trigger a hot-reload endpoint if implemented)
3. No code changes required anywhere else in the pipeline

---

## Layer 1 — Intent Classification, Table Routing, and SQL Plan (Single LLM Call)

### Purpose
Determine what the user is asking, which table answers it, and what the SQL logic
should be — in a single Vertex AI call. Parallelized with a fast in-memory keyword
lookup that runs simultaneously.

### Intent Types
The agent classifies every query into one of these intent categories:
- `aggregation` — sum, count, average of a metric
- `trend` — metric over time
- `comparison` — one dimension vs another
- `lookup` — specific rows matching a condition
- `ranking` — top N or bottom N by a metric
- `anomaly` — outliers, drops, spikes

The intent type is used downstream in the answer generator to decide the chart type
and the shape of the natural language answer.

### Parallel Execution at L1

Two threads fire simultaneously the moment the user submits a query:

**Thread A — Keyword Lookup (< 5ms)**

Uses the inverted keyword index built at startup. Tokenizes the user query,
looks up each token in the index, scores tables by hit count, returns the
top 2 candidate tables. This is a deterministic, zero-cost sanity check.
It does not make the routing decision alone — it is used to validate or
resolve conflicts with the LLM routing output.

**Thread B — Combined LLM Call (600–800ms)**

System prompt contains:
- The agent's role and strict output format instructions
- A compact version of the schema registry: for each table, only the
  `table_id`, `display_name`, `description`, and `business_tags` (not full columns —
  full columns come in Layer 2 after the table is selected)
- The conversation history from the current session (last 5 turns) so
  follow-up questions are resolved in context

User message contains:
- The raw user question

Required output format (strict JSON, no prose):
```
{
  "intent": one of the intent type strings above,
  "table_id": the fully-qualified BQ table ID selected from the registry (primary fact or single table),
  "join_pattern": one of join_allowlist query pattern ids (e.g. fact_sales_with_dims), or null if single-table only,
  "confidence": float between 0 and 1 representing routing confidence,
  "entities": list of business entities mentioned (metric names, dimension values, etc.),
  "time_range": structured time range object with start and end in ISO 8601,
               or null if no time range specified,
  "plan": ordered list of 3-5 strings, each describing one logical step of the SQL query
          in plain English (no SQL syntax in the plan)
}
```

The LLM is instructed via system prompt to return only this JSON object, with no
preamble, no explanation, and no markdown formatting.

### Fan-In and Conflict Resolution

After both threads complete:

- If Thread B confidence >= 0.85: use Thread B's `table_id` as the routing decision.
- If Thread B confidence < 0.85: compare Thread B's selection with Thread A's top candidate.
  - If they agree: proceed with that table, treat as high confidence.
  - If they disagree: use the clarification flow described below.
- If Thread B returns a `table_id` not present in the registry: this is a hallucination.
  Fall back to Thread A's top candidate.

### Clarification Flow

Triggered only when routing confidence is irresolvably low. The agent sends a single
short question to the user via SSE before proceeding. Example: if the user says
"show me performance last month" and two tables are plausible candidates, the agent
asks "Do you mean sales performance or agent performance?" The user's answer is
appended to the conversation history and the L1 call re-fires with the clarification included.
This flow adds one round trip but is preferable to querying the wrong table.

### Follow-Up Question Handling

If the session has prior turns, the L1 system prompt includes the last resolved `table_id`,
the last generated SQL, and the last extracted entities. The LLM is instructed to
inherit unchanged context (same table, same filters) unless the new question explicitly
changes them. This allows "now filter by region APAC" to correctly modify the prior
SQL rather than generating a new query from scratch.

---

## Layer 2 — SQL Generation

### Purpose
Generate a single, valid, executable BigQuery Standard SQL query using the table
selected in L1, the plan from L1, the full table schema, and retrieved few-shot examples.

### Inputs Assembled Before the LLM Call (all from memory, < 10ms total)

1. Full schema of the selected table (from registry — all columns, types, descriptions, sample values)
2. Top 2 most semantically similar few-shot (question, sql) pairs for this table,
   retrieved by cosine similarity between the user question embedding and the
   pre-computed few-shot embedding matrix. User question embedding is computed
   once at the start of the request and reused here.
3. The plan array from the L1 JSON output
4. The user's original question
5. The resolved time range from L1 (injected as a concrete date filter, not left to the LLM to interpret)

### SQL Generation System Prompt Contents

- Role: BigQuery SQL expert
- Hard constraints (all mandatory, stated as absolute rules):
  - Use only columns listed in the schema below. Never reference any other column.
  - Use only the table ID as written. Never modify or guess the table name.
  - Use BigQuery Standard SQL syntax only. No legacy SQL.
  - Always use fully-qualified column references (table_alias.column_name) when joining.
  - Apply the time range filter exactly as provided in the resolved time range input.
  - Add LIMIT 1000 unless the plan explicitly requires all rows.
  - Never use SELECT *. Always name the columns explicitly.
  - Do not include explanations, prose, or markdown. Return SQL only.
- The full table schema
- The 2 retrieved few-shot examples
- The plan from L1

### LLM Call

Single call. The plan from L1 means the LLM does not need to reason about query
structure — it only needs to translate each plan step into SQL syntax with the
schema in front of it. This makes the call faster and less error-prone than
a zero-shot or single-shot plan-and-generate approach.

Output: raw SQL string only.

### Time Range Injection

Time ranges are never left to the LLM to compute. The L1 output includes a
structured `time_range` object. Before the L2 call, the backend resolves this
to concrete ISO 8601 date strings (e.g., "last month" → `2025-04-01` to `2025-04-30`)
and injects them as literal values into the system prompt. The LLM is told exactly
what date range to use. This eliminates a large class of hallucinations where
the LLM guesses date math incorrectly.

**Structured L1 output:** Use Vertex **controlled generation** / JSON schema or response MIME type constraints for the L1 model where supported, so `table_id` and enums are not free-form prose.

---

## Layer 3 — Parallel SQL Validation

### Purpose
Validate the generated SQL across three independent dimensions simultaneously before
it touches BigQuery. All three validators run in parallel. All three must pass before
execution proceeds. No validator can be skipped.

### Validator A — Column Existence Check (< 20ms)

Uses the `sqlglot` library to parse the generated SQL into an AST (with **BigQuery dialect** enabled).
Extracts every column reference from the AST.
Checks each column reference against the schema registry for the **set of tables allowed in this query** (single table or join allowlist).
If any referenced column does not exist in the registry: validation fails.
Failure message includes the hallucinated column name and the list of valid columns.
This is the primary defense against column hallucination.

**Limitation:** Complex BigQuery constructs (`UNNEST`, deep `STRUCT`/`ARRAY` paths, some analytic functions) may parse differently or hide references; treat Validator A as **strong but not mathematically complete** — BigQuery dry run (Validator B) remains mandatory.

### Validator B — BigQuery Dry Run (300–500ms)

Submits the SQL to the BigQuery Jobs API with `dryRun=True`.
This call returns bytes scanned and catches all syntax errors without executing the query.
It costs nothing (dry runs are free).
If the dry run fails: validation fails. The BQ error message is captured verbatim
and used in the retry prompt.
If the dry run passes: the bytes-scanned value is checked against the cost gate threshold
(configurable, default 10GB). If over threshold, the agent sends a warning SSE event
to the frontend before proceeding ("This query will scan 45GB. Proceeding...").

### Validator C — Safety Check (< 5ms)

Parses the SQL AST with sqlglot and checks for:
- Presence of any DML statement: UPDATE, DELETE, INSERT, MERGE, TRUNCATE, DROP, CREATE, ALTER
- Table references not present in the schema registry (cross-dataset injection attempt)
- Absence of any FROM clause (pathological output)
If any check fails: validation fails immediately and the query is rejected without retry.
Safety failures are logged as security events and are never retried.

### Retry Logic

If Validator A or Validator B fails (not Validator C), the pipeline retries L2 SQL
generation exactly once. The retry prompt includes:
- All original L2 inputs
- The exact validation error message
- An explicit instruction to fix only the identified problem

If the retry also fails validation, the agent returns a structured error to the user
explaining that it could not generate a valid query for this question, and suggests
the user rephrase or be more specific. It does not return a hallucinated answer.

Maximum retries: 1. This bounds worst-case latency.

---

## Layer 4 — BigQuery Execution

### Purpose
Execute the validated SQL query on BigQuery and return results as a structured
Python object for downstream use.

### Client Configuration

The BigQuery client is initialized once at FastAPI application startup, not per request.
It uses a service account with the minimum required IAM roles:
- `roles/bigquery.jobUser` — to submit query jobs
- `roles/bigquery.dataViewer` — to read from the specific datasets

The client is stored as a module-level singleton and reused across all requests.

### Execution Parameters

- Timeout: 30 seconds. If BQ does not return within 30s, the request fails with a
  timeout error sent to the frontend via SSE.
- Result fetch: Use the BigQuery Storage Read API for result sets larger than 1000 rows.
  Use the default REST API for smaller results. The Storage Read API is 3-5x faster
  for large result fetches.
- Row limit: The SQL always contains LIMIT 1000 (enforced in L2). This bounds execution
  time and result payload size.

### Result Handling

After execution, the result is converted to a Python list of dicts (serializable to JSON).

Special cases:
- Zero rows returned: flag as `empty_result=True`. This flows into the answer generator,
  which tells the user no data was found for their query. The agent never fabricates rows.
- Result has more than 50 columns: reduce to the columns referenced in the SQL SELECT
  clause only. This should not occur given LIMIT 1000 and no SELECT *, but is a safety net.
- BQ runtime error (non-syntax, e.g., resource exceeded): captured and sent to frontend
  as a structured error SSE event. Not retried (these are infrastructure errors, not LLM errors).

### Result Caching

A Redis instance (Cloud Memorystore) caches query results keyed by a hash of
(table_id + normalized_sql). TTL: 5 minutes. On a cache hit, the pipeline skips
L4 entirely and uses the cached result. This primarily benefits dashboards or
cases where the same user asks the same question twice in a session.

**Invalidation:** Do not rely on automatic “table updated” signals for all BigQuery load patterns. **v1:** TTL-only eviction is acceptable. **v2+:** If you need stronger freshness, tie invalidation to your **known** ETL completion (Pub/Sub from your pipeline), or shorten TTL for specific tables.

---

## Layer 5 — Streaming Answer Generation

### Purpose
Convert the BigQuery result set into a natural language answer that streams token-by-token
to the frontend. Also determine whether a chart is appropriate and emit a chart specification.

### Pre-conditions for This Call

The answer generation LLM call fires only after:
- L4 has returned results (or empty_result flag)
- The results have been serialized to JSON

The full result set (up to 1000 rows) is injected into the prompt as the data source.
The LLM is instructed to summarize only what is in the data. It is explicitly forbidden
from using any external knowledge to augment the answer.

**Note:** Narrative answers can still mis-state numbers vs the table. Mitigations: keep the **DataTable** as the source of truth in the UI; optionally add **deterministic** post-processing for KPIs (e.g. sum of a column) when the question maps to a single aggregate.

### System Prompt Contents for Answer Generation

- Role: data analyst summarizing a query result for a business user
- Hard constraints:
  - Only reference numbers and values present in the data provided
  - Do not speculate, extrapolate, or add context not in the data
  - If the result is empty, say so clearly and suggest why the query may have returned nothing
  - Write in plain business English, not technical language
  - Keep the summary under 150 words unless the data complexity requires more
- The user's original question
- The SQL that was executed (for the LLM's reference, not to be quoted in the answer)
- The full result set as a JSON array
- Chart decision instructions: determine if the data is best shown as a chart.
  If yes, decide the chart type based on intent (trend→line, comparison→bar,
  breakdown→pie, multi-metric→composed). Emit chart configuration at the end of
  the response in a structured block that the frontend can parse. If no chart is
  appropriate, omit the chart block entirely.

### Streaming to the UI (Jaybel v1: via Agent Engine)

The L5 LLM uses Vertex AI streaming. The **agent / tools layer** forwards chunks to the UI.
In v1 the Next.js app consumes **Agent Engine stream** responses and maps them to the
event types below (equivalent to SSE payloads; no requirement for `GET /api/query/stream`
on the query hot path).

Optional: a FastAPI SSE endpoint may exist for **local pipeline debugging only**.

### UI event sequence (Complete)

These event types are emitted in order throughout the full pipeline (from agent tools):

1. `{type: "status", message: "Analyzing your question..."}` — emitted after L1 starts
2. `{type: "table_name", table: "project.dataset.sales_transactions", display: "Sales Transactions"}` — emitted after L1 fan-in resolves the table
3. `{type: "status", message: "Generating query..."}` — emitted when L2 starts
4. `{type: "sql", sql: "SELECT ..."}` — emitted after L3 validation passes
5. `{type: "status", message: "Running query..."}` — emitted when L4 starts
6. `{type: "cost_warning", bytes_scanned: 15000000000}` — emitted only if BQ dry run exceeds cost gate
7. `{type: "results", rows: [...], row_count: 42, columns: [...]}` — emitted when L4 completes
8. `{type: "token", text: "..."}` × N — each LLM output token streamed individually
9. `{type: "chart_spec", chart_type: "bar", x: "region", y: "total_revenue", title: "..."}` — emitted if chart is appropriate (parsed from end of L5 output)
10. `{type: "done", session_id: "...", query_id: "..."}` — pipeline complete, triggers UI download bar
11. `{type: "error", code: "...", message: "..."}` — emitted on any failure, replaces steps 4–10

The frontend maps Agent Engine stream payloads to these types and renders each
to the appropriate UI component as it arrives.

---

## Layer 6 — Session Memory

### Purpose
Maintain conversation continuity within and across sessions. Enable follow-up questions
to correctly reference prior query context without the user having to repeat themselves.

### Per-Session State (in-session, in-memory during request)

Stored in FastAPI request state and persisted to **local PostgreSQL** after each turn:
- `session_id` — UUID generated at session creation
- `user_id` — from authentication context
- `turns` — ordered list of turn objects, each containing:
  - `question` — raw user question
  - `intent` — classified intent from L1
  - `table_id` — routing decision from L1
  - `entities` — extracted entities from L1
  - `time_range` — resolved time range
  - `sql` — final executed SQL
  - `row_count` — result row count
  - `answer` — full generated answer text
  - `chart_type` — if a chart was generated
  - `timestamp` — UTC timestamp

Only the last 5 turns are injected into L1's context window. Older turns are
stored in Postgres but not sent to the LLM (to keep prompt size bounded).

### Cross-Session Memory (Vertex AI agent memory / Memory Bank)

For persistent user-level memory across different sessions, use the **Memory Bank** (or equivalent) feature in Vertex AI Agent Builder for your SDK version. Confirm the exact service class name in current documentation for your region.

What gets stored in the memory bank:
- User's most frequently queried tables
- User's preferred time ranges (e.g., user always asks about "last quarter")
- Dimension preferences (e.g., user always filters by a specific region)
- Vocabulary mapping (e.g., user says "bookings" to mean the `confirmed_orders` table)

What is never stored in the memory bank:
- Raw SQL (session-specific, not portable)
- PII from query results
- Result data

Memory bank entries are injected into the L1 system prompt as a "user context" block.
They are soft hints, not hard constraints — the LLM can override them when the
current question clearly differs from the user's usual patterns.

### PostgreSQL schema (local app data)

Migrations `001`–`004`:

- **`users`** — local user identity; optional `sales_rep_code` for rep-scoped questions
- **`chat_sessions`** — `id`, `user_id`, `title`, `agent_engine_session_id`, `ui_context` (JSONB: `last_starter_id`, `last_category_id`)
- **`chat_turns`** — question, intent, `table_id`, sql, answer, `results_sample`, `events`, optional `starter_id` / `category_id`, `feedback_rating` / `feedback_comment`

**History into pipeline:** FastAPI builds last 5 turns from `chat_turns` and sends `[SALES_CONTEXT]{history, history_json, sales_rep_code}[/SALES_CONTEXT]` in the Agent Engine message; `agent.py` parses and calls `Pipeline.run(history=...)`.

Default dev user UUID: `00000000-0000-4000-8000-000000000001` (`dev@localhost`).

**Not used in v1:** Firestore / Firebase.

---

## Layer 7 — UI (Chatbot Interface + Charts + Reports)

### Overview

The UI is a full-screen chat interface in the style of Claude.ai. It has a session
sidebar on the left and a chat window on the right. The agent message component
is the most complex — it progressively renders status indicators, streaming text,
a collapsible SQL block, a paginated data table, an optional chart, and a download bar,
all driven by the SSE event stream.

### Authentication (local v1)

No Firebase. The local FastAPI uses a **default dev user** from Postgres (`users` table) or
a simple email field on login later. Pass `user_id` and optional `sales_rep_code` into Agent
Engine session context for rep-scoped questions.

All session and chat history APIs require the local API; there is no Firestore.

### Layout and Components

**ChatShell**
Top-level layout component. Renders `SessionSidebar` on the left and `ChatWindow`
on the right. Manages global state: current session ID (local dev user is implicit).

**SessionSidebar**
Displays a list of past sessions loaded from `GET /api/sessions`.
Each item shows session title and `updated_at`.
Clicking a session loads turns via `GET /api/sessions/{session_id}/turns`.
New session: `POST /api/sessions`.
Includes a "New Chat" button that clears the chat window and creates a new session.
Sessions are grouped by date (Today, Yesterday, Last 7 days, Older).

**ChatWindow**
Renders `MessageList` and `InputBar`. Manages the SSE connection via `useChatStream` hook (local API).
On user message submit: adds the user message to `MessageList`, creates an empty
agent message placeholder, opens the SSE stream, and progressively fills the
agent message as SSE events arrive.

**MessageList**
Renders an ordered list of `UserMessage` and `AgentMessage` components.
Auto-scrolls to bottom on new content. Preserves scroll position when
the user scrolls up to read history.

**UserMessage**
Simple chat bubble with the user's question text and timestamp.

**AgentMessage**
The primary complex component. It is a state machine driven by SSE events.
It renders the following sub-components in sequence as events arrive:

  - `StatusIndicator` — shows the current pipeline status message. Updates as each
    status SSE event arrives. Disappears when `done` event arrives.
  
  - `StreamingText` — renders answer tokens one by one as `token` events arrive.
    Uses a typewriter-style character append. Stops when `done` arrives.
  
  - `SQLAccordion` — collapsed by default. Triggered by `sql` SSE event.
    When expanded, shows the SQL in a syntax-highlighted code block.
    Includes a copy-to-clipboard button.
  
  - `DataTable` — triggered by `results` SSE event. Renders results as a
    sortable, paginated table. Client-side pagination (all rows already in browser
    state). Columns are auto-detected from the result schema. Numeric columns are
    right-aligned and formatted with locale-aware number formatting.
    Shows row count and table name in the header.
  
  - `ChartPanel` — triggered by `chart_spec` SSE event. Conditionally rendered.
    Uses Recharts. Supported chart types: LineChart, BarChart, PieChart, ComposedChart.
    Chart is responsive (fills the available width). Includes axis labels, tooltip,
    and legend. Chart title comes from the `chart_spec` event.
  
  - `DownloadBar` — triggered by `done` SSE event. Shows three buttons:
    Download CSV, Download PDF Report, Download Chart PNG.
    Buttons only appear after the full pipeline completes.

**Chat input** (in `ChatWindow`)
Text area + Send. Disabled while streaming. Starters **fill the input** (user edits, then sends).

### Question discovery (Phase C+ — implemented)

See `docs/UI_QUESTION_DISCOVERY_PLAN.md`.

| Feature | Implementation |
|---------|----------------|
| Categories | 11 cards in **ExploreDrawer** (`GET /api/question-catalog/categories`) |
| Starters | 97 from `content/question_catalog.yaml`; badges: full / partial / target not in BQ |
| Browse UX | **Browse questions** → slide-over drawer; breadcrumb `Explore / {category}` |
| Search | Text + filters: `category_id`, `intent`, `table_id` |
| Follow-ups | `FollowUpChips` after last answer; curated + rules; **Show more** if &gt;5 |
| Rep category | **My Performance** disabled until `sales_rep_code` in sidebar |
| Feedback | Thumbs + optional comment → `POST /api/sessions/{id}/turns/{turn_id}/feedback` |
| Session search | Sidebar `?q=` on `GET /api/sessions` |
| Chart + table | Sticky side-by-side when both present |

### useChatStream Hook

Manages the full SSE lifecycle. On activation:
1. `POST /api/chat/stream` with `{ session_id, question, starter_id?, category_id? }`
2. Forwards SSE events (`status`, `sql`, `results`, `token`, `chart_spec`, `cost_warning`)
3. Final `done` from API includes `turn_id` (Postgres row) for follow-ups and feedback
4. Closes on `done` or `error`

### Chart Export (PNG)

When the user clicks "Download Chart PNG":
1. The `ChartPanel` component renders the Recharts chart to an off-screen canvas
   using `html2canvas`
2. The canvas is converted to a PNG blob
3. A download is triggered in-browser, no backend call required
The PNG includes the chart title and a timestamp in the filename.

### CSV Export

When the user clicks "Download CSV":
1. The result rows already in frontend state are serialized using `Papa.unparse`
2. A CSV blob is created and downloaded in-browser, no backend call required
The CSV includes a header row matching the column names from the result schema.
The filename includes the session ID and a timestamp.

### PDF Report Generation (Backend)

When the user clicks "Download PDF Report":
1. Frontend calls `POST /api/report/generate` with the current session's last turn data:
   - question, answer, sql, row_count, table_id, chart_type
2. Backend:
   a. Retrieves full result rows for that query ID from the session state or re-fetches from cache
   b. Renders a PDF using WeasyPrint. The PDF includes:
      - Report title (the user's question)
      - Generation timestamp and table queried
      - Natural language answer section
      - SQL query section (code-formatted)
      - Data table (up to 100 rows; remainder noted as truncated)
      - Chart image (if applicable, rendered server-side using matplotlib or sent as base64 from frontend)
   c. Uploads the PDF to Cloud Storage: `gs://{report_bucket}/{user_id}/{session_id}/{query_id}.pdf`
   d. Generates a signed URL with 15-minute expiry
   e. Returns the signed URL to the frontend
3. Frontend triggers a browser download from the signed URL

### Session API Endpoints (Local FastAPI — Postgres)

`POST /api/sessions`
Creates a row in `chat_sessions` for the current user. Returns `session_id`.

`GET /api/sessions`
Returns sidebar list: `{session_id, title, updated_at}` ordered by `updated_at` desc.

`GET /api/sessions/{session_id}/turns`
Returns turn history from `chat_turns` for the session.

`DELETE /api/sessions/{session_id}`
Deletes session and cascaded turns.

`POST /api/chat/stream`
Main SSE endpoint. Body: `{session_id, question}`. Proxies Agent Engine `stream_query`,
forwards pipeline events to the browser, persists turn on `done`. No Firebase token.

`POST /api/report/generate`
Accepts turn data, generates and uploads a PDF, returns a signed GCS URL.

---

## GCP Infrastructure

### Services Used

**Vertex AI**
- LLM inference: gemini-2.5-flash (or your chosen GA model) for all three LLM calls (L1, L2, L5)
- Embeddings: current Vertex **text embedding** model for table embeddings and few-shot embeddings
  (computed once at startup, not per request)
- Memory: Vertex AI Agent / Memory Bank feature set you enable in your project (verify SDK class names and availability in your region)
- **Agent Engine:** agent definition, tools pointing at Cloud Run, and auth as described in the deployment section above

**BigQuery**
- Primary data store for all queryable tables
- Dry run API for validation
- Storage Read API for fast result fetch on large result sets
- Optionally: a `query_logs` table to store all executed queries and their results
  for the evaluation framework

**PostgreSQL (local, v1)**
- Session and turn storage on developer machine (`docker compose` or native Postgres)
- Schema: `sql/migrations/001_initial.sql`

**Cloud Memorystore (Redis)** — deferred
- Query result cache keyed by (table_id + normalized_sql)
- TTL: 5 minutes

**Cloud Storage**
- Report bucket: generated PDF reports
- Schema bucket (optional): YAML files for the schema registry, if external storage is preferred
  over repo-bundled files. Lifecycle policy: delete reports after 7 days.

**Cloud Run** — deferred (v1 uses local FastAPI on port 8000)

**Frontend hosting (v1)**
- Next.js: `npm run dev` → `http://localhost:3000`
- FastAPI: `uvicorn` → `http://localhost:8000`
- Production hosting deferred until after local v1 works

### Service Account IAM Roles

The backend runs under a dedicated service account with only these roles:
- `roles/bigquery.jobUser` — submit BQ jobs
- `roles/bigquery.dataViewer` — read from specific datasets (grant at dataset level, not project level)
- ~~`roles/datastore.user`~~ — not used (Postgres is local, not GCP Firestore)
- `roles/storage.objectAdmin` — read/write report bucket only (scoped to the specific bucket)
- `roles/aiplatform.user` — call Vertex AI APIs
- `roles/redis.editor` — read/write Memorystore

No project-level admin roles. Principle of least privilege.

---

## Evaluation Framework

### What to Instrument

Every pipeline execution writes a structured log row to a BigQuery table `pipeline_logs`
with the following fields:
- `query_id` — UUID per request
- `session_id`
- `user_id`
- `timestamp`
- `question` — raw user input
- `intent` — L1 output
- `table_id_selected` — L1 routing decision
- `routing_confidence` — L1 confidence score
- `l1_latency_ms`
- `sql_generated` — L2 output
- `validation_a_passed` — boolean (column check)
- `validation_b_passed` — boolean (dry run)
- `validation_c_passed` — boolean (safety)
- `retry_count` — 0 or 1
- `bytes_scanned`
- `bq_execution_ms`
- `row_count`
- `empty_result` — boolean
- `answer_text`
- `chart_generated` — boolean
- `total_pipeline_ms`
- `error_code` — null if success

### Metrics to Compute from Logs

**Routing Accuracy**
Requires a ground truth dataset of (question → correct table) pairs, labeled manually.
Metric: top-1 accuracy. Alert if it drops below 90%.

**SQL Correctness**
- Dry run pass rate on first attempt: `COUNT WHERE retry_count=0 AND validation_b_passed` / total
- Column hallucination rate: `COUNT WHERE validation_a_passed=false` / total
- These are measurable without a human label — the validators provide the signal.

**Empty Result Rate**
High empty result rate on a given table may indicate schema drift (column renamed, data moved).
Alert if it exceeds 15% of queries for a given table.

**Latency Percentiles**
Compute p50, p90, p99 of `total_pipeline_ms` and `bq_execution_ms` daily from logs.

**Hallucination Rate**
The column existence validator (Layer 3A) is the primary signal. Every failure is a caught
hallucination. Log it, measure it by table and by LLM version.

---

## Latency Budget (Expected at Runtime)

```
Step                                 Expected Latency
──────────────────────────────────────────────────────
Keyword lookup (Thread A, parallel)  < 5ms
L1 LLM call (Thread B, parallel)     600–800ms
Schema + few-shot retrieval           < 10ms (in-memory)
L2 SQL generation LLM call           800–1000ms
L3 Parallel validation               350–500ms (bounded by BQ dry run)
L4 BQ execution                      500ms–4s (query-dependent)
L5 first token to frontend           ~200ms after L4 completes (streaming)
──────────────────────────────────────────────────────
Non-BQ latency total                 ~2.1s
Perceived latency to first output    ~1.3s (table name shown during L1)
Worst case (slow BQ + 1 retry)       ~8s (still streaming, user sees progress)
Cache hit case                       ~1.5s (skips L4)
```

---

## Implementation Order (Jaybel v1 — phased)

Build in this order. Steps marked **(defer)** are documented but not required for first working agent + localhost UI.

### Phase A — Core pipeline library (`pipeline/`) — **complete**

**Scope:** BigQuery + Vertex only. No Firebase, no Postgres. Optional `user_context` (`sales_rep_code`, `user_id`) for rep-scoped SQL when Phase C passes local user from Postgres.

1. Schema registry loader + keyword index + join allowlist loader  
   (Test: load 13 YAMLs; keyword hits for “sales”, “working days”, “new business”)

2. BigQuery client + dry-run validator  
   (Test: known-good / known-bad SQL)

3. Column + safety validators (sqlglot, join-aware allowlist)  
   (Test: hallucinated column / illegal join fails)

4. L1 routing JSON (`table_id`, `join_pattern`, `time_range`, `plan`)  
   (Test: Q001–Q020 from `docs/qa_evaluation_set.yaml`)

5. L2 SQL generation + time-range injection (Australia/Sydney)  
   (Test: few-shot questions dry-run pass)

6. L3 orchestrator + single retry  
7. L4 execute + empty-result handling  
8. L5 answer + chart_spec parsing  

9. End-to-end pipeline function emitting UI event sequence  
   (Test: 5 sample questions without UI)

### Phase B — Agent Engine — **complete** (redeploy after `agent.py` changes: history, `history_json`)

10. Agent definition + tools wrapping Phase A — **done** (`agent/sales_analytics_agent/agent.py`, ID `8991351443894042624`)  
11. Deploy to `jaybel-dev` / `us-central1` — **done**  
12. IAM: runtime SA → BigQuery + Vertex AI — verify in GCP  

App sessions are **not** stored in Agent Engine; Phase C Postgres owns chat history. Agent Engine sessions are transport/telemetry only.

### Question discovery UI (Phase C+) — **complete**

See `docs/UI_QUESTION_DISCOVERY_PLAN.md`.

- `content/question_catalog.yaml` — 97 starters, categories, follow-ups, rules (`scripts/build_question_catalog.py`)
- `GET/POST /api/question-catalog/*` — categories, starters, search (category/intent/table filters), follow-ups
- `POST /api/chat/stream` — optional `starter_id` / `category_id`; last 5 turns as `[SALES_CONTEXT]` + `history_json`; SSE `done` includes `turn_id`
- `chat_sessions.ui_context` — persists last starter/category; used for follow-up resolution
- Next.js: explore drawer, category breadcrumb, follow-up chips (show more), thumbs + comment, session search, sticky chart/table split
- Tests: `tests/test_catalog_integrity.py`, `tests/test_q031_q032_history.py`, `tests/test_question_catalog.py`, `tests/test_chat_history.py`

### Phase C — Local UI + PostgreSQL — **complete**

13. Postgres: `docker-compose up -d` (host port **15433**), migrations `001`–`004`  
14. FastAPI: `backend/` — sessions, turns, `PATCH /api/sessions/me`, chat SSE proxy, question catalog  
15. Next.js: charts, downloads, cost warning, rep profile, grouped sidebar, table UX  
16. Tests: `tests/test_phase_c_api.py` (with `DATABASE_URL`)  
17. Run: `./scripts/start-phase-c.sh` then uvicorn + `npm run dev` (see README)

### Phase D — Quality — **next**

18. QA runner: routing accuracy + dry-run pass rate on Q001–Q097  
19. Handle `requires_target_table` / `requires_rep_context` cases per glossary  

### Deferred (v1.1+)

- Redis cache  
- FastAPI `/api/query/stream` debug-only  
- PDF + GCS (server-side; client CSV/PNG/print work today)  
- Memory Bank  
- `pipeline_logs` BQ table  
- Cloud Run production backend  
- Load testing / p99 SLO tuning  
- UI-4: LLM follow-ups, command palette, mobile sheet

---

## Buildability (honest assessment)

**Yes, this is buildable** as a custom NL→SQL stack on GCP: schema registry + routing + SQL generation + dry run + allowlist checks is a proven pattern. **Caveats:**

- **“Zero hallucination”** is a product goal, not a theorem: you **minimize** wrong SQL and wrong narratives via validators, retries, and UI that privileges tabular results. Dry run + column checks catch most SQL issues; natural language summaries still benefit from optional deterministic KPIs.
- **Agent Engine** adds integration and IAM work but does not block the core pipeline; Jaybel v1 uses **in-agent tools**, not Cloud Run callbacks.
- **Multi-table analytics** needs one of the explicit strategies above; the original single-table assumption is the main functional risk for “sales” questions.
- **Startup embedding pre-compute** on every Cloud Run instance can slow cold start / scale-out; consider lazy embedding, prebuilt vector files in GCS, or reducing tables/examples if startup misses SLOs.

---

## Information to provide (checklist for the implementer)

### Provided by product owner (Jaybel)
- [x] Project `jaybel-dev`, region `us-central1`
- [x] Service account `115724636423-compute@developer.gserviceaccount.com`
- [x] 13-table schema (PDF → YAML registry; **validated vs live BQ**)
- [x] Glossary and 97-case QA set (incl. Office Supplies client questions)
- [x] Agent Engine–only entry
- [x] No policy v1
- [x] Timezone `Australia/Sydney` (calendar-relative dates)
- [x] UI v1: **localhost** (Next.js + FastAPI)
- [x] App storage: **local PostgreSQL** (not Firebase) — see `docs/ARCHITECTURE_LOCAL.md`
- [x] Agent Engine deployed — ID in `agent/AGENT_ENGINE_RESOURCE.env`

### Phase C + question discovery (done in repo)
- [x] `backend/` FastAPI + Postgres + catalog API + history envelope
- [x] `frontend/` Next.js (explore drawer, follow-ups, feedback, session search)
- [x] `content/question_catalog.yaml` + `scripts/build_question_catalog.py`
- [x] QA YAML: `category` on all 97 cases
- [x] Tests: `test_phase_c_api`, `test_question_catalog`, `test_chat_history`, `test_catalog_integrity`, `test_q031_q032_history`
- [x] Agent Engine redeployed with `SALES_CONTEXT` / `history_json` parsing
- [ ] On your Mac: run stack for manual testing (`./scripts/start-phase-c.sh`, uvicorn, `npm run dev`)
- [ ] Phase D QA runner automation
- [ ] Optional: dedicated non-default compute SA for production

---

## Plan correctness summary

| Area | Verdict |
|------|--------|
| Schema registry + live BQ | **Validated** — all 13 tables |
| L1/L2 + `join_pattern` | **Sound** (Jaybel join allowlist) |
| Validators (sqlglot + dry run + safety) | **Sound** — join-aware for facts |
| Time range (Australia/Sydney) | **Locked** |
| Agent Engine entry + in-agent tools | **Aligned** (streaming → UI events) |
| Client targets / projections | **Scoped** — honest partial answers until budget tables |
| Redis / Cloud Run SSE hot path | **Deferred** — not v1 blockers |
| L5 answer faithfulness | **Risk** — mitigate with DataTable as source of truth |
| Full readiness | **`docs/FINAL_READINESS_REVIEW.md`** |

---
