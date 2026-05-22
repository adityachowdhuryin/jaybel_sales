-- Link local chat session to Vertex AI Agent Engine session (follow-ups)
ALTER TABLE chat_sessions
    ADD COLUMN IF NOT EXISTS agent_engine_session_id TEXT;
