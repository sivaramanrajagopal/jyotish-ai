# Supabase analytics dashboard — query list

Copy-paste queries for **Supabase → SQL Editor**. Save each as a **favorite** (star icon) for a quick dashboard.

**Setup (one time):**
1. Run `supabase/analytics_views.sql` — creates helper views
2. Optional: run `supabase/analytics_events.sql` — server-side product events (pairs with GA4)

Run queries as **postgres** (SQL Editor default) — bypasses RLS so you see all users.

---

## Quick health check

### App snapshot (run daily)
```sql
SELECT
  (SELECT COUNT(*) FROM auth.users)                    AS total_auth_users,
  (SELECT COUNT(*) FROM public.users)                  AS total_public_users,
  (SELECT COUNT(*) FROM natal_charts)                  AS charts_saved,
  (SELECT COUNT(*) FROM natal_charts WHERE chart_data IS NOT NULL) AS full_charts,
  (SELECT COUNT(*) FROM user_locations)                AS users_with_location,
  (SELECT COUNT(*) FROM ai_usage WHERE usage_date = CURRENT_DATE) AS ai_users_today;
```

---

## Users & auth

### 1 — All users with last login
```sql
SELECT
  u.email,
  u.name,
  u.subscription_tier,
  u.created_at AT TIME ZONE 'Asia/Kolkata'     AS registered_ist,
  au.last_sign_in_at AT TIME ZONE 'Asia/Kolkata' AS last_login_ist,
  (nc.id IS NOT NULL)                          AS has_chart
FROM public.users u
LEFT JOIN auth.users au ON au.id = u.id
LEFT JOIN natal_charts nc ON nc.user_id = u.id
ORDER BY au.last_sign_in_at DESC NULLS LAST;
```

### 2 — New sign-ups (last 30 days)
```sql
SELECT * FROM v_signups_daily
WHERE signup_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY signup_date;
```

### 3 — Signed up but no chart
```sql
SELECT u.email, u.created_at
FROM public.users u
LEFT JOIN natal_charts nc ON nc.user_id = u.id
WHERE nc.id IS NULL
ORDER BY u.created_at DESC;
```

### 4 — Active users (logged in last 7 days)
```sql
SELECT COUNT(*) AS active_7d
FROM auth.users
WHERE last_sign_in_at >= NOW() - INTERVAL '7 days';
```

### 5 — Chart saved but missing full JSON (needs recalculate)
```sql
SELECT u.email, nc.calculated_at
FROM natal_charts nc
JOIN public.users u ON u.id = nc.user_id
WHERE nc.chart_data IS NULL
ORDER BY nc.calculated_at DESC;
```

---

## Location & geography

### 6 — Birth places (top 20)
```sql
SELECT * FROM v_birth_places LIMIT 20;
```

### 7 — Current cities (where users set location)
```sql
SELECT * FROM v_user_cities LIMIT 20;
```

### 8 — Users: birth place vs current city
```sql
SELECT
  u.email,
  nc.birth_form->>'place_of_birth' AS birth_place,
  ul.city                            AS current_city,
  ul.timezone,
  ul.updated_at AT TIME ZONE 'Asia/Kolkata' AS location_set_ist
FROM public.users u
JOIN natal_charts nc ON nc.user_id = u.id
LEFT JOIN user_locations ul ON ul.user_id = u.id
ORDER BY ul.updated_at DESC NULLS LAST;
```

### 9 — Users outside India (birth place text match)
```sql
SELECT
  u.email,
  nc.birth_form->>'place_of_birth' AS birth_place,
  nc.moon_sign,
  nc.calculated_at
FROM natal_charts nc
JOIN public.users u ON u.id = nc.user_id
WHERE nc.birth_form->>'place_of_birth' NOT ILIKE '%india%'
  AND nc.birth_form->>'place_of_birth' NOT ILIKE '%chennai%'
  AND nc.birth_form->>'place_of_birth' NOT ILIKE '%mumbai%'
  AND nc.birth_form->>'place_of_birth' NOT ILIKE '%bangalore%'
  AND nc.birth_form->>'place_of_birth' NOT ILIKE '%delhi%'
  AND nc.birth_form->>'place_of_birth' NOT ILIKE '%hyderabad%'
  AND nc.birth_form->>'place_of_birth' NOT ILIKE '%coimbatore%'
ORDER BY nc.calculated_at DESC;
```

### 10 — Panchangam cache coverage by city
```sql
SELECT
  location_name,
  MIN(date) AS earliest_date,
  MAX(date) AS latest_date,
  COUNT(*)  AS days_cached
FROM panchangam_daily
GROUP BY location_name
ORDER BY days_cached DESC;
```

---

## Charts & astrology profile

### 11 — Moon sign distribution
```sql
SELECT * FROM v_moon_sign_distribution;
```

### 12 — Ascendant distribution
```sql
SELECT ascendant, COUNT(*) AS users
FROM natal_charts
WHERE ascendant IS NOT NULL
GROUP BY ascendant
ORDER BY users DESC;
```

### 13 — Recent chart calculations
```sql
SELECT
  u.email,
  nc.sun_sign,
  nc.moon_sign,
  nc.ascendant,
  nc.birth_form->>'place_of_birth' AS place,
  nc.calculated_at AT TIME ZONE 'Asia/Kolkata' AS calculated_ist
FROM natal_charts nc
JOIN public.users u ON u.id = nc.user_id
ORDER BY nc.calculated_at DESC
LIMIT 50;
```

---

## AI usage (Step 7)

### 14 — AI usage today by user
```sql
SELECT
  u.email,
  a.chat_count,
  a.forecast_count,
  a.chat_count + a.forecast_count AS total_ai_calls
FROM ai_usage a
JOIN public.users u ON u.id = a.user_id
WHERE a.usage_date = CURRENT_DATE
ORDER BY total_ai_calls DESC;
```

### 15 — AI usage trend (last 14 days)
```sql
SELECT * FROM v_ai_usage_daily
WHERE usage_date >= CURRENT_DATE - INTERVAL '14 days'
ORDER BY usage_date;
```

### 16 — Heavy AI users (last 7 days)
```sql
SELECT
  u.email,
  SUM(a.chat_count)     AS chats,
  SUM(a.forecast_count) AS forecasts
FROM ai_usage a
JOIN public.users u ON u.id = a.user_id
WHERE a.usage_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY u.email
HAVING SUM(a.chat_count) + SUM(a.forecast_count) >= 10
ORDER BY chats + forecasts DESC;
```

---

## Personal Panchangam / Tara

### 17 — Today's Tara distribution (all users)
```sql
SELECT * FROM v_tara_today;
```

### 18 — Users in Chandra Ashtama today
```sql
SELECT
  u.email,
  udp.natal_moon_rasi,
  udp.today_moon_sign,
  udp.ashtama_start,
  udp.ashtama_end
FROM user_daily_panchangam udp
JOIN public.users u ON u.id = udp.user_id
WHERE udp.date = CURRENT_DATE
  AND udp.is_chandra_ashtama = TRUE;
```

### 19 — Personal panchangam job coverage
```sql
SELECT
  date,
  COUNT(DISTINCT user_id) AS users_computed
FROM user_daily_panchangam
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY date
ORDER BY date DESC;
```

---

## Optional: app_events (if you ran analytics_events.sql)

### 20 — Events last 7 days
```sql
SELECT
  event_name,
  COUNT(*) AS events,
  COUNT(DISTINCT user_id) AS unique_users
FROM app_events
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY event_name
ORDER BY events DESC;
```

### 21 — Funnel: chart → chat (same user, 7 days)
```sql
WITH chart_users AS (
  SELECT DISTINCT user_id FROM app_events
  WHERE event_name = 'chart_calculated'
    AND created_at >= NOW() - INTERVAL '7 days'
),
chat_users AS (
  SELECT DISTINCT user_id FROM app_events
  WHERE event_name = 'chat_sent'
    AND created_at >= NOW() - INTERVAL '7 days'
)
SELECT
  (SELECT COUNT(*) FROM chart_users) AS calculated_chart,
  (SELECT COUNT(*) FROM chat_users)  AS sent_chat,
  (SELECT COUNT(*) FROM chart_users c JOIN chat_users t ON c.user_id = t.user_id) AS chart_then_chat;
```

---

## GA4 companion (Google Analytics 4)

GA4 does **not** live in Supabase. Use GA4 for **traffic & behaviour**; use Supabase for **users, charts, locations, AI usage**.

**GA4 property:** link your Vercel site `https://jyotish-ai-zeta.vercel.app`

### Recommended GA4 reports (Explorations)

| Report | GA4 path | Mirrors Supabase query |
|--------|----------|------------------------|
| Daily users | Reports → Engagement → Overview | Query #2 sign-ups (Supabase has accounts; GA4 has visitors) |
| Top pages | Reports → Engagement → Pages | Home vs My Chart vs Ask AI tab usage |
| Geo — City | Reports → User → Demographics → City | Query #6–9 birth/current location |
| Traffic source | Reports → Acquisition → Traffic acquisition | Marketing / organic split |
| Events | Reports → Engagement → Events | Custom events below |

### Custom GA4 events to add in frontend (recommended)

| Event name | When | Params |
|------------|------|--------|
| `chart_calculated` | POST /natal-chart success | `place`, `has_account` |
| `sign_in` | Magic link completed | `method: email` |
| `tab_view` | Tab change | `tab`: home, chart, chat, forecast, panchangam |
| `chat_sent` | Chat message sent | `language` |
| `forecast_view` | Forecast tab loaded | `transit_date` |

Add to Vercel with `gtag.js` or `@vercel/analytics` + GA4 measurement ID `G-XXXXXXXX`.

### GA4 BigQuery (optional, advanced)

If you link GA4 → BigQuery, example query for daily active users:

```sql
-- Run in BigQuery, NOT Supabase
SELECT
  event_date,
  COUNT(DISTINCT user_pseudo_id) AS dau
FROM `your_project.analytics_XXXXX.events_*`
WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY))
  AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
  AND event_name = 'page_view'
GROUP BY event_date
ORDER BY event_date DESC;
```

### Side-by-side weekly dashboard

| Metric | Supabase query | GA4 |
|--------|----------------|-----|
| Registered users | `#2` sign-ups daily | N/A (use Supabase) |
| Charts saved | App snapshot `charts_saved` | Event `chart_calculated` |
| AI chat volume | `#15` ai_usage trend | Event `chat_sent` count |
| Top birth cities | `#6` birth places | Geo map (approximate from IP) |
| Returning users | `#4` active 7d | GA4 Retention report |

---

## Supabase Dashboard UI (optional)

Supabase **does not** have built-in chart dashboards for custom SQL yet. Options:

1. **SQL Editor favorites** — star each query above
2. **Metabase / Grafana** — connect read-only to Supabase Postgres
3. **Supabase + Retool** — build admin panel with these queries
4. **Google Looker Studio** — connect GA4 + optional Supabase connector

---

## Privacy note

These queries contain **PII** (email, birth place, DOB). Restrict SQL Editor access to admins only. Never expose query results publicly.
