ALTER TABLE chat_turns
    ADD COLUMN IF NOT EXISTS feedback_rating SMALLINT,
    ADD COLUMN IF NOT EXISTS feedback_comment TEXT;
