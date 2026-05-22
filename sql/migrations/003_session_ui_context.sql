ALTER TABLE chat_sessions
    ADD COLUMN IF NOT EXISTS ui_context JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE chat_turns
    ADD COLUMN IF NOT EXISTS starter_id TEXT,
    ADD COLUMN IF NOT EXISTS category_id TEXT;
