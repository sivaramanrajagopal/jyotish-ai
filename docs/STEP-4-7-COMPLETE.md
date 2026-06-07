# Steps 4–7 — Server charts, RLS, privacy, AI limits

Complete after Steps 1–3 (production config, Supabase Auth, backend JWT).

## A. Run SQL in Supabase (Step 5)

1. Supabase → **SQL Editor**
2. Paste and run **`supabase/schema_steps_4_5_7.sql`**

This adds:
- `chart_data` + `birth_form` columns on `natal_charts`
- `auth.users` → `public.users` trigger + backfill
- RLS policies for user-owned rows
- `ai_usage` table for daily quotas

## B. Render env (optional quotas)

| Variable | Default | Purpose |
|----------|---------|---------|
| `AI_DAILY_CHAT_LIMIT` | 40 | Max chat requests per user per day |
| `AI_DAILY_FORECAST_LIMIT` | 25 | Max forecast AI calls per user per day |

## C. What changed

### Step 4 — Server-side chart
- Full chart stored in `natal_charts.chart_data` on calculate
- `GET /natal-chart` returns saved chart (JWT required)
- Chat, forecast, ashtakavarga load chart from DB when Bearer token present

### Step 5 — RLS + auth.users
- New sign-ups auto-create `public.users` row
- RLS: users only read/write their own charts

### Step 6 — No localStorage PII
- Birth data removed from `localStorage`
- Anonymous users: **sessionStorage only** (24h, cleared on tab close)
- Signed-in users: chart lives on server

### Step 7 — AI quotas + moderation
- Daily per-user limits on chat + forecast AI routes
- Prompt-injection / script tags blocked in chat messages

## D. Verify

1. Sign in → calculate chart → Supabase **natal_charts** has `chart_data` JSON
2. DevTools → Application → **no** `jyotish-chart-v1` in localStorage
3. Network → `/chat` request body has **no** `natal_chart` when signed in
4. `GET /natal-chart` returns your chart with Bearer token

## E. Security plan complete

| Step | Status |
|------|--------|
| 1 Production config | ✅ |
| 2 Supabase Auth | ✅ |
| 3 Backend JWT | ✅ |
| 4 Server chart storage | ✅ |
| 5 RLS + auth trigger | ✅ (run SQL) |
| 6 Remove localStorage PII | ✅ |
| 7 AI quotas + moderation | ✅ |
