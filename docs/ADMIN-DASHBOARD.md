# Owner admin dashboard

In-app analytics for the app owner — users, locations, AI usage, sign-ups.

## Setup

### 1. Supabase (one time)

Run in SQL Editor:
- `supabase/analytics_views.sql`

### 2. Render (backend)

| Variable | Value |
|----------|--------|
| `ADMIN_EMAILS` | `adtrackmail@gmail.com` (comma-separated for multiple owners) |
| `ADMIN_TOKEN` | (optional — for curl/scripts with `X-Admin-Token`) |
| `SUPABASE_JWT_SECRET` | Required so your JWT is verified |

Redeploy after saving.

### 3. Vercel (frontend)

No extra env var required — the app calls `GET /auth/me` and shows the Admin tab when `is_admin` is true.

Optional for local dev only: `VITE_ADMIN_EMAILS` (same list as Render).

## How to use

1. Sign in on the app with your owner email (magic link)
2. An **Admin** tab appears in the nav (desktop + mobile)
3. Open it to see the dashboard

Direct link: `https://jyotish-ai-zeta.vercel.app/?tab=admin`

## API routes (owner only)

| Route | Data |
|-------|------|
| `GET /admin/overview` | Totals snapshot |
| `GET /admin/users` | User list with chart/location |
| `GET /admin/locations` | Birth places + current cities |
| `GET /admin/ai-usage` | Daily AI call trend |
| `GET /admin/signups` | Daily sign-up trend |

Auth: Bearer JWT (owner email) **or** header `X-Admin-Token`.

## curl example

```bash
curl -s https://YOUR-BACKEND.onrender.com/admin/overview \
  -H "Authorization: Bearer YOUR_SUPABASE_ACCESS_TOKEN"
```

Or with admin token:

```bash
curl -s https://YOUR-BACKEND.onrender.com/admin/overview \
  -H "X-Admin-Token: YOUR_ADMIN_TOKEN"
```

## Security

- Admin tab is **hidden** unless `VITE_ADMIN_EMAILS` matches your signed-in email
- Backend **rejects** non-owner JWTs with 403
- PII never exposed to other users
- Do not put `ADMIN_EMAILS` or tokens in public repos

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No Admin tab | Set `ADMIN_EMAILS` on Render, redeploy backend, sign in with that email |
| 403 on dashboard | `ADMIN_EMAILS` on Render must include your signed-in email |
| Empty data | Run `analytics_views.sql`; ensure users/charts exist in Supabase |
| Last login blank | Run `schema_steps_4_5_7.sql` so `v_users_overview` joins `auth.users` |
