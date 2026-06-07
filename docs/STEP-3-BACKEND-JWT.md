# Step 3 of 7 — Backend JWT verification

The backend now verifies Supabase Bearer tokens. Forged `user_id` values in the request body or URL are rejected.

## A. Render environment variable

Add to **Render → your service → Environment**:

| Variable | Where to find it |
|----------|------------------|
| `SUPABASE_JWT_SECRET` | Supabase → **Project Settings → API → JWT Settings → JWT Secret** |

This is **not** the anon key or service role key. It is the JWT signing secret used to verify access tokens.

Redeploy Render after saving.

## B. What changed in code

| File | Change |
|------|--------|
| `backend/auth.py` | Verify JWT, `get_current_user`, `resolve_user_id` |
| `backend/main.py` | `GET /auth/me`, `/natal-chart` binds `user_id` from JWT |
| `backend/agents/ashtama_agent.py` | `/today/{user_id}` and `/location/{user_id}` require JWT |

## C. Route behaviour

| Route | Auth |
|-------|------|
| `POST /natal-chart` | Anonymous OK; `user_id` only saved when Bearer token valid and matches |
| `GET /auth/me` | Requires Bearer token |
| `GET /personal-panchangam/today/{user_id}` | Requires Bearer token; path must match JWT |
| `PUT /personal-panchangam/location/{user_id}` | Requires Bearer token; path must match JWT |
| `POST /chat`, `POST /forecast`, etc. | Still anonymous (Step 4 will load chart server-side) |

## D. Verify

1. Sign in on [https://jyotish-ai-zeta.vercel.app](https://jyotish-ai-zeta.vercel.app)
2. DevTools → Network → copy `Authorization: Bearer …` from a request
3. Test:

```bash
curl -s https://YOUR-BACKEND.onrender.com/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected: `{"user_id":"...","email":"..."}`

4. Calculate a chart while signed in → Supabase **Table Editor → natal_charts** should have your `user_id`
5. Try sending a fake `user_id` without a token → `401`

## E. Next step

**Step 4** — Load chart from Supabase by authenticated user instead of trusting client-sent `natal_chart` JSON on AI/forecast routes.

See also `docs/STEP-2-SUPABASE-AUTH.md` and `SECURITY.md`.
