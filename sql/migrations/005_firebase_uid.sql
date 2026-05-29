-- Link app users to Firebase Auth UIDs (Google OAuth).
ALTER TABLE users ADD COLUMN IF NOT EXISTS firebase_uid TEXT UNIQUE;

CREATE INDEX IF NOT EXISTS idx_users_firebase_uid ON users (firebase_uid);
