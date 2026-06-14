-- Prashna (horary) session history for signed-in users
-- Run in Supabase SQL editor (optional — guest history stays in browser)

CREATE TABLE IF NOT EXISTS prashna_sessions (
  id            BIGSERIAL PRIMARY KEY,
  user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  question      TEXT NOT NULL,
  category      TEXT NOT NULL,
  question_time TIMESTAMPTZ NOT NULL,
  timezone      TEXT NOT NULL DEFAULT 'Asia/Kolkata',
  place_label   TEXT,
  lat           DOUBLE PRECISION,
  lon           DOUBLE PRECISION,
  verdict       TEXT NOT NULL,
  result_json   JSONB NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prashna_sessions_user_created
  ON prashna_sessions (user_id, created_at DESC);

ALTER TABLE prashna_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users read own prashna sessions"
  ON prashna_sessions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users insert own prashna sessions"
  ON prashna_sessions FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users delete own prashna sessions"
  ON prashna_sessions FOR DELETE
  USING (auth.uid() = user_id);
