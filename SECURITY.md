# Security Review — Parashara Jyotish

Production security audit (OWASP Top 10). Last updated: 2026-06-06.

## Executive summary

| Area | Status |
|------|--------|
| API keys in frontend | ✅ Pass — only `VITE_API_URL` exposed |
| Supabase RLS | ⚠️ Partial — patch SQL provided; Auth not wired |
| SQL injection | ✅ Pass — parameterized Supabase SDK only |
| Authentication | ❌ Gap — anonymous API; user_id routes disabled in prod |
| XSS | ✅ Pass — React escaping; no `dangerouslySetInnerHTML` |
| Rate limiting | ✅ Fixed — SlowAPI middleware + per-route limits |
| Secrets in frontend | ✅ Pass |
| Data leakage (errors/logs) | ✅ Fixed — generic client errors; no body logging |
| Logging sensitive data | ✅ Fixed — 422 handler no longer logs request body |
| OWASP Top 10 | ⚠️ A01/A07 remain until Supabase Auth ships |

---

## 1. API key exposure

**Finding:** ✅ No OpenAI, Supabase service role, or admin tokens in frontend source.

- Frontend: `VITE_API_URL` only (`src/api/client.js`)
- Backend: all secrets via `os.getenv()` in `.env` (gitignored)
- **Action:** Never add `VITE_SUPABASE_SERVICE_KEY` or LLM keys to frontend

---

## 2. Supabase RLS policies

**Findings:**

| Issue | Severity | Fix |
|-------|----------|-----|
| `users.id` not FK to `auth.users` | High | Run `supabase/schema_security_patch.sql` after Auth setup |
| `FOR ALL` policies without `WITH CHECK` | Medium | Patch splits into SELECT/INSERT/UPDATE/DELETE |
| `user_daily_panchangam` / `user_locations` no user read policies | High | Patch adds `auth.uid() = user_id` policies |
| Backend uses **service role** (bypasses RLS) | Critical | Requires app-layer auth before user-scoped writes |

**Apply:** `supabase/schema_security_patch.sql` in Supabase SQL Editor when enabling Auth.

---

## 3. SQL injection

**Finding:** ✅ No raw SQL in HTTP handlers. All queries use Supabase Python SDK (`.eq()`, `.upsert()`).

Offline SQL bulk scripts in `supabase/panchangam_sql/` are admin-only, not HTTP-exposed.

---

## 4. Authentication weaknesses

**Finding:** ❌ No end-user JWT validation. Client sends full `natal_chart` on every AI call.

**Implemented mitigations:**
- `GET/PUT /personal-panchangam/{user_id}` → **404 in production** (`APP_ENV=production`)
- Frontend only uses `/personal-panchangam/anonymous`

**Required before multi-user production:**
1. Supabase Auth (email/OAuth)
2. Backend verifies `Authorization: Bearer <jwt>`
3. Store charts server-side; API accepts `chart_id` not raw dict
4. Replace service-role writes with user JWT + RLS

---

## 5. XSS vulnerabilities

**Finding:** ✅ Pass

- Chat/forecast render AI text as React text nodes
- `renderBoldSafe()` only allows `**bold**` — no HTML
- Backend `_sanitise()` strips HTML tags from chat input
- **Added:** CSP headers via `frontend/vercel.json`

---

## 6. Rate limiting

**Implemented (`backend/rate_limit.py`, `main.py`):**

- `SlowAPIMiddleware` registered (enforces `default_limits`)
- X-Forwarded-For aware client IP (Render/Vercel proxy)
- Limits on: `/`, `/ping`, `/panchangam/*`, `/sky/today`, `/personal-panchangam/*`, all AI routes
- Admin bulk-preload: **5/hour**

---

## 7. Secrets in frontend code

**Finding:** ✅ Pass — grep confirms no hardcoded secrets.

---

## 8. Data leakage

**Implemented fixes:**

| Vector | Fix |
|--------|-----|
| Exception strings in HTTP 500/503 | Generic messages; details server-side only |
| 422 validation logs full body | Body removed from logs (PII: DOB, name, chat) |
| Admin bulk-preload error_details | Returns date + status only |
| CORS on 500 errors | Origin echoed only if in `ALLOWED_ORIGINS` |
| localStorage chart PII | Documented risk — migrate to Auth + server storage |

---

## 9. Logging sensitive information

**Fixed:** Validation handler logs path + field errors only.

**Recommendation:** On Render, set log retention; avoid `print()` for errors — use `logging` (partially done).

---

## 10. OWASP Top 10 mapping

| ID | Risk | Status |
|----|------|--------|
| A01 Broken Access Control | user_id IDOR, client chart trust | ⚠️ Mitigated (prod block); Auth needed |
| A02 Cryptographic Failures | Admin token in query | ✅ Fixed → `X-Admin-Token` header |
| A03 Injection | LLM prompt injection via crafted chart | ⚠️ Mitigated — size limits + field sanitise |
| A04 Insecure Design | Anonymous full-chart API | Documented; Auth planned |
| A05 Misconfiguration | Docs in prod off ✅; HSTS added ✅; CSP added ✅ |
| A06 Vulnerable Components | Pin requirements.txt | Ongoing — run `pip audit` |
| A07 Auth failures | No user auth | ❌ Planned |
| A08 Data integrity | Client natal_chart | ⚠️ `validate_client_natal_chart()` |
| A09 Logging failures | PII in logs | ✅ Fixed |
| A10 SSRF | Geocoding outbound calls | Low — rate limited |

---

## Files added/changed in this hardening pass

```
backend/rate_limit.py          — X-Forwarded-For aware limiter
backend/security.py            — admin token, body size, chart validation, CORS helper
backend/main.py                  — middleware, error sanitisation, rate limits
backend/agents/ashtama_agent.py — rate limits, prod route block, input validation
backend/agents/chat_agent.py   — fail closed if chart context fails
frontend/vercel.json           — CSP + security headers
frontend/public/sw.js          — URL/tab whitelist for notifications
supabase/schema_security_patch.sql — RLS hardening
```

---

## Deployment checklist

- [ ] Set `APP_ENV=production` on Render
- [ ] Set strong `ADMIN_TOKEN` (32+ random bytes); use `X-Admin-Token` header for bulk-preload
- [ ] Set `ALLOWED_ORIGINS` to exact Vercel URL(s) — no trailing slashes
- [ ] Confirm `OPENAI_API_KEY` and `SUPABASE_SERVICE_KEY` only in Render env
- [ ] Run `schema_security_patch.sql` when enabling Supabase Auth
- [ ] Update `vercel.json` `connect-src` with your exact Render backend URL
- [ ] Enable HTTPS only (Vercel + Render default)

---

## Admin API usage (post-fix)

```bash
# OLD (insecure — do not use):
# POST /panchangam/bulk-preload?admin_token=SECRET

# NEW:
curl -X POST "https://your-backend.onrender.com/panchangam/bulk-preload?days=30&location=Chennai" \
  -H "X-Admin-Token: YOUR_ADMIN_TOKEN"
```
