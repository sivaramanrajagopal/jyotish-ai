-- schema_steps_4_5_7.sql
-- Run in Supabase SQL Editor AFTER schema.sql + schema_ashtama.sql
-- Steps 4–7: full chart storage, auth.users sync, RLS, AI usage quotas

-- ── Step 4: store full chart JSON server-side ────────────────────────────────
ALTER TABLE natal_charts ADD COLUMN IF NOT EXISTS chart_data JSONB;
ALTER TABLE natal_charts ADD COLUMN IF NOT EXISTS birth_form JSONB;

-- ── Step 5: sync auth.users → public.users ───────────────────────────────────
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.users (id, email, name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1))
  )
  ON CONFLICT (id) DO UPDATE
    SET email = EXCLUDED.email,
        updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Backfill existing auth users into public.users (safe to re-run)
INSERT INTO public.users (id, email, name)
SELECT
  id,
  email,
  COALESCE(raw_user_meta_data->>'name', split_part(email, '@', 1))
FROM auth.users
ON CONFLICT (id) DO UPDATE
  SET email = EXCLUDED.email,
      updated_at = NOW();

-- ── Step 5: RLS hardening (from schema_security_patch.sql) ───────────────────
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

DROP POLICY IF EXISTS "udp_self_read" ON user_daily_panchangam;
CREATE POLICY "udp_self_read" ON user_daily_panchangam
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "alerts_self_read" ON ashtama_alerts;
CREATE POLICY "alerts_self_read" ON ashtama_alerts
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "locations_service_write" ON user_locations;
DROP POLICY IF EXISTS "locations_self_rw" ON user_locations;
CREATE POLICY "locations_self_rw" ON user_locations
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── Step 7: daily AI usage quotas ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_usage (
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    usage_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    chat_count  INTEGER NOT NULL DEFAULT 0,
    forecast_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, usage_date)
);

ALTER TABLE ai_usage ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "ai_usage_self" ON ai_usage;
CREATE POLICY "ai_usage_self" ON ai_usage
  FOR SELECT USING (auth.uid() = user_id);
