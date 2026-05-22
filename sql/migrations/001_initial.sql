-- Jaybel Sales Analytics — local app schema (PostgreSQL)
-- Chat/session storage only; analytics remain in BigQuery.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    display_name TEXT NOT NULL DEFAULT 'Local User',
    sales_rep_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New chat',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_updated
    ON chat_sessions (user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS chat_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    query_id TEXT NOT NULL,
    question TEXT NOT NULL,
    intent TEXT,
    table_id TEXT,
    join_pattern TEXT,
    sql TEXT,
    answer TEXT,
    row_count INTEGER DEFAULT 0,
    chart_spec JSONB,
    results_sample JSONB,
    events JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_turns_session_created
    ON chat_turns (session_id, created_at ASC);

-- Default dev user for local-only use (no Firebase)
INSERT INTO users (id, email, display_name, sales_rep_code)
VALUES (
    '00000000-0000-4000-8000-000000000001',
    'dev@localhost',
    'Local Developer',
    NULL
)
ON CONFLICT (email) DO NOTHING;
