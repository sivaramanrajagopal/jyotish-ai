-- analytics_events.sql (optional)
-- Lightweight server-side event log — complements GA4 page-view data.
-- Run once if you want product events queryable in Supabase alongside GA4.

CREATE TABLE IF NOT EXISTS app_events (
  id          BIGSERIAL PRIMARY KEY,
  user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
  event_name  TEXT NOT NULL,          -- e.g. chart_calculated, chat_sent, sign_in
  properties  JSONB NOT NULL DEFAULT '{}',
  -- properties examples: { "tab": "forecast", "city": "Chennai", "language": "tamil" }
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS app_events_name_time_idx
  ON app_events (event_name, created_at DESC);

CREATE INDEX IF NOT EXISTS app_events_user_idx
  ON app_events (user_id, created_at DESC);

ALTER TABLE app_events ENABLE ROW LEVEL SECURITY;

-- Users can insert their own events; admins use service role to read all
CREATE POLICY "app_events_insert_own" ON app_events
  FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "app_events_service_read" ON app_events
  FOR SELECT USING (auth.role() = 'service_role');

-- Example insert from backend (service role):
-- INSERT INTO app_events (user_id, event_name, properties)
-- VALUES ('uuid', 'chart_calculated', '{"place":"Chennai, India"}');
