# Step 2 of 7 — Supabase Auth (frontend)

Adds magic-link sign-in, session persistence, and `Authorization: Bearer` on API calls.
Backend JWT verification is **Step 3** — routes still work anonymously until then.

## A. Supabase Dashboard

1. Open **Authentication → Providers → Email** and enable **Email**.
2. Optional: disable **Confirm email** if you want instant magic-link access in dev.
3. **Authentication → URL Configuration**:
   - **Site URL**: `https://jyotish-ai-zeta.vercel.app`
   - **Redirect URLs** (add all that apply):
     - `https://jyotish-ai-zeta.vercel.app/**`
     - `http://localhost:5173/**`

## B. Vercel environment variables

| Variable | Where to find it |
|----------|------------------|
| `VITE_SUPABASE_URL` | Supabase → Project Settings → API → Project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase → Project Settings → API → anon public |

Keep using `VITE_API_URL` from Step 1. **Never** put the service role key on Vercel.

Redeploy after saving variables.

## C. Local development

```bash
cd frontend
cp .env.example .env.local
# Edit .env.local with your Supabase URL + anon key
npm run dev
```

## D. What the app does now

- **Sign in** button in the header (compact) and full form on Home when expanded.
- Magic link email → user returns to the app → session stored by Supabase JS.
- All API requests include `Authorization: Bearer <jwt>` when signed in.
- **Calculate chart** sends `user_id` so the backend can store the chart in `natal_charts` (if Supabase is enabled on Render).

Auth UI is always shown on Home. Magic link works once `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set on Vercel and redeployed.

## E. Verify

1. Deploy with env vars → open app → **Sign in** appears in header.
2. Enter email → receive magic link → click → header shows signed-in state.
3. DevTools → Network → any `/natal-chart` request has `Authorization` header.
4. Supabase → **Authentication → Users** shows the new user.
5. After calculating a chart while signed in, check **Table Editor → natal_charts** for a row with your `user_id`.

## F. Next step

**Step 3** — Backend verifies JWT (`backend/auth.py`, `Depends(get_current_user)`) and rejects forged `user_id` values.

See also `docs/STEP-1-PRODUCTION-CONFIG.md` and `SECURITY.md`.
