-- analytics_views.sql
-- Run once in Supabase SQL Editor (as postgres / service role).
-- Powers saved dashboard queries below. Safe to re-run (CREATE OR REPLACE).

-- ── 1. User + chart snapshot ─────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_users_overview AS
SELECT
  u.id,
  u.email,
  u.name,
  u.subscription_tier,
  u.created_at                                          AS registered_at,
  au.last_sign_in_at,
  au.email_confirmed_at,
  nc.calculated_at                                      AS chart_saved_at,
  nc.sun_sign,
  nc.moon_sign,
  nc.ascendant,
  nc.birth_form->>'place_of_birth'                      AS birth_place,
  nc.birth_form->>'dob'                                 AS birth_dob,
  nc.birth_form->>'gender'                              AS birth_gender,
  (nc.chart_data IS NOT NULL)                           AS has_full_chart,
  COALESCE(ul.city, nc.birth_form->>'place_of_birth')   AS current_city,
  ul.timezone                                           AS current_timezone,
  ul.updated_at                                         AS location_updated_at
FROM public.users u
LEFT JOIN auth.users au ON au.id = u.id
LEFT JOIN natal_charts nc ON nc.user_id = u.id
LEFT JOIN user_locations ul ON ul.user_id = u.id;

-- ── 2. Daily sign-ups ───────────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_signups_daily AS
SELECT
  DATE(created_at AT TIME ZONE 'Asia/Kolkata') AS signup_date,
  COUNT(*)                                     AS new_users
FROM auth.users
GROUP BY 1
ORDER BY 1 DESC;

-- ── 3. Birth place distribution ─────────────────────────────────────────────
CREATE OR REPLACE VIEW v_birth_places AS
SELECT
  COALESCE(NULLIF(TRIM(nc.birth_form->>'place_of_birth'), ''), 'Unknown') AS birth_place,
  COUNT(*)                                                                AS users
FROM natal_charts nc
WHERE nc.birth_form IS NOT NULL
GROUP BY 1
ORDER BY users DESC;

-- ── 4. Current location distribution ────────────────────────────────────────
CREATE OR REPLACE VIEW v_user_cities AS
SELECT
  ul.city,
  ul.timezone,
  COUNT(*) AS users
FROM user_locations ul
GROUP BY ul.city, ul.timezone
ORDER BY users DESC;

-- ── 5. AI usage rollup ───────────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_ai_usage_daily AS
SELECT
  usage_date,
  SUM(chat_count)      AS total_chat_calls,
  SUM(forecast_count)  AS total_forecast_calls,
  COUNT(DISTINCT user_id) AS active_ai_users
FROM ai_usage
GROUP BY usage_date
ORDER BY usage_date DESC;

-- ── 6. Personal panchangam / Tara today ───────────────────────────────────────
CREATE OR REPLACE VIEW v_tara_today AS
SELECT
  udp.date,
  udp.tara_name,
  udp.tara_nature,
  COUNT(*) AS users
FROM user_daily_panchangam udp
WHERE udp.date = CURRENT_DATE
GROUP BY udp.date, udp.tara_name, udp.tara_nature
ORDER BY users DESC;

-- ── 7. Moon sign distribution (user base) ───────────────────────────────────
CREATE OR REPLACE VIEW v_moon_sign_distribution AS
SELECT
  COALESCE(nc.moon_sign, 'Unknown') AS moon_sign,
  COUNT(*)                          AS users
FROM natal_charts nc
GROUP BY 1
ORDER BY users DESC;
