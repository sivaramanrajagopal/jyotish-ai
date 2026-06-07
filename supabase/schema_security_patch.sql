-- schema_security_patch.sql
-- Run in Supabase SQL Editor AFTER schema.sql + schema_ashtama.sql
-- Hardens RLS before enabling Supabase Auth in production.

-- ── 1. Tie users.id to auth.users (required for auth.uid() policies) ─────────
-- Only run on fresh installs or after migrating existing users.
-- ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey;
-- ALTER TABLE users ALTER COLUMN id DROP DEFAULT;
-- ALTER TABLE users ADD CONSTRAINT users_auth_fk FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- ── 2. Split blanket FOR ALL policies into explicit CRUD ─────────────────────

DROP POLICY IF EXISTS "users_self" ON users;
CREATE POLICY "users_select_self" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "users_insert_self" ON users FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "users_update_self" ON users FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);
CREATE POLICY "users_delete_self" ON users FOR DELETE USING (auth.uid() = id);

DROP POLICY IF EXISTS "natal_charts_self" ON natal_charts;
CREATE POLICY "natal_charts_select" ON natal_charts FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "natal_charts_insert" ON natal_charts FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "natal_charts_update" ON natal_charts FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "natal_charts_delete" ON natal_charts FOR DELETE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "forecasts_self" ON forecasts;
CREATE POLICY "forecasts_select" ON forecasts FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "forecasts_insert" ON forecasts FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "forecasts_update" ON forecasts FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "forecasts_delete" ON forecasts FOR DELETE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "chat_history_self" ON chat_history;
CREATE POLICY "chat_history_select" ON chat_history FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "chat_history_insert" ON chat_history FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "chat_history_update" ON chat_history FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "chat_history_delete" ON chat_history FOR DELETE USING (auth.uid() = user_id);

-- ── 3. Per-user ashtama tables — read/write own rows (when using anon JWT) ───

CREATE POLICY IF NOT EXISTS "udp_self_read" ON user_daily_panchangam
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "alerts_self_read" ON ashtama_alerts
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "locations_service_write" ON user_locations;
CREATE POLICY "locations_self_rw" ON user_locations
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- FK integrity (run once auth.users is linked)
-- ALTER TABLE user_daily_panchangam
--   ADD CONSTRAINT user_daily_panchangam_user_fk
--   FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
