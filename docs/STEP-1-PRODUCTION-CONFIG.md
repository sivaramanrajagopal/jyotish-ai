# Step 1 of 7 — Production configuration

Complete this before moving to Step 2 (Supabase Auth).

## Your checklist

### A. Render (backend)

Open **Render → your service → Environment** and set:

| Variable | Example | Required |
|----------|---------|----------|
| `APP_ENV` | `production` | Yes |
| `ALLOWED_ORIGINS` | `https://your-app.vercel.app` | Yes — exact URL, no trailing slash |
| `OPENAI_API_KEY` | `sk-proj-...` | Yes for AI features |
| `SUPABASE_URL` | `https://xxx.supabase.co` | Yes for Panchangam cache |
| `SUPABASE_SERVICE_KEY` | `eyJ...` (service role) | Yes for backend DB |
| `ADMIN_TOKEN` | run `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` | Yes for bulk preload |

**Do NOT** put `SUPABASE_SERVICE_KEY` or `OPENAI_API_KEY` on Vercel.

### B. Vercel (frontend)

Open **Vercel → Project → Settings → Environment Variables**:

| Variable | Example |
|----------|---------|
| `VITE_API_URL` | `https://your-backend.onrender.com` |

Redeploy after saving.

### C. Verify

1. Open your Vercel app URL — chart calculation works
2. Open browser DevTools → Network — API calls go to Render HTTPS URL
3. Backend logs on Render should **not** show `PRODUCTION MISCONFIG` errors

### D. Admin bulk-preload (optional)

```bash
curl -X POST "https://YOUR-BACKEND.onrender.com/panchangam/bulk-preload?days=7&location=Chennai" \
  -H "X-Admin-Token: YOUR_ADMIN_TOKEN"
```

---

## When done

Reply **"Step 1 done"** and we will implement **Step 2: Supabase Auth (login UI + JWT)**.

## Next steps preview

| Step | Topic |
|------|--------|
| 2 | Supabase Auth — login/signup |
| 3 | Backend JWT verification |
| 4 | Server-side chart storage |
| 5 | RLS SQL patch |
| 6 | Remove localStorage PII |
| 7 | AI quotas + moderation |
