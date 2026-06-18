# Documentation index

Start here when spinning up, debugging production, or extending features.

## New developer path

1. [../README.md](../README.md) — clone, env, run locally (5 min)
2. [DEVELOPER-GUIDE.md](./DEVELOPER-GUIDE.md) — architecture, DB, API, auth, deploy, debugging
3. [FEATURES-TECHNICAL-REFERENCE.md](./FEATURES-TECHNICAL-REFERENCE.md) — Career, Health, Bhavam, chat grounding, SW issues

## Setup & production

| Doc | When to read |
|-----|----------------|
| [STEP-1-PRODUCTION-CONFIG.md](./STEP-1-PRODUCTION-CONFIG.md) | First deploy to Render + Vercel |
| [STEP-2-SUPABASE-AUTH.md](./STEP-2-SUPABASE-AUTH.md) | Magic link auth |
| [STEP-3-BACKEND-JWT.md](./STEP-3-BACKEND-JWT.md) | JWT verification on API |
| [STEP-4-7-COMPLETE.md](./STEP-4-7-COMPLETE.md) | Chart storage, AI quotas, analytics |

## Operations

| Doc | When to read |
|-----|----------------|
| [FEATURES-TECHNICAL-REFERENCE.md §11](./FEATURES-TECHNICAL-REFERENCE.md#11-production-troubleshooting-matrix) | Production incident matrix |
| [DEVELOPER-GUIDE.md §16](./DEVELOPER-GUIDE.md#16-debugging-playbook) | Symptom → fix playbook |
| [SUPABASE-ANALYTICS-DASHBOARD.md](./SUPABASE-ANALYTICS-DASHBOARD.md) | Analytics SQL + views |
| [ADMIN-DASHBOARD.md](./ADMIN-DASHBOARD.md) | Owner admin tab |
| [../SECURITY.md](../SECURITY.md) | Secrets, RLS, quotas |

## Feature deep dives

All in [FEATURES-TECHNICAL-REFERENCE.md](./FEATURES-TECHNICAL-REFERENCE.md):

- Career (D1 + D10, PDF10 rules)
- Health (D3, body map, transits)
- Bhavat Bhavam
- Tamil Doshas, Indu Lagna
- Chat AI context blocks
- Service worker / PWA

## SQL migrations

Run in Supabase SQL Editor (order matters):

```
supabase/schema_steps_4_5_7.sql
supabase/schema_security_patch.sql
supabase/anon_ai_usage.sql
supabase/analytics_events.sql
supabase/analytics_views.sql
supabase/prashna_sessions.sql
```

See DEVELOPER-GUIDE §7 for table reference.
