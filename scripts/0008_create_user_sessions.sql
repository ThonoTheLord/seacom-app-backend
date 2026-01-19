-- scripts/0008_create_user_sessions.sql
-- Add table to persist ephemeral user sessions (presence)

CREATE TABLE IF NOT EXISTS user_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role text NOT NULL,
  session_id text NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  last_seen timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_role_active_lastseen
  ON user_sessions (role, is_active, last_seen DESC);

-- TTL / cleanup: optional background job should remove old inactive rows later.