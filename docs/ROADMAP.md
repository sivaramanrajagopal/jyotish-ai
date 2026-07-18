# Jyotish AI — Product Roadmap

**Last updated:** 2026-07-18
**Audience:** Founder / product owner (plain-language, non-jargon)

This is the "what's done, what's next, and why" plan for taking the app live and
turning it into a paid product. Read top to bottom.

---

## Where we are today (honest snapshot)

**Working and in production:**

- Natal chart calculation (Swiss Ephemeris, Lahiri sidereal, Aquarius-lagna golden chart verified)
- Full feature set: Chart, Career, Health, Dosha Radar, House Links, Bhavam, Gochara,
  Panchangam, Prashna, Chat (Ask AI), Forecast, and the new **Life Cycle Simulator**
- **Life Cycle in chat** — ask a timing question and get a short, dated, hallucination-safe answer
- Login/accounts (Supabase)
- **Free usage limits** — daily AI caps for guests and signed-in users
- **Panchangam cache** — 2 years (2026–2027) × 7 cities pre-loaded in Supabase ✅ *(confirmed loaded)*
- Analytics, rate limiting, account deletion

- **Legal pages** — Terms, Privacy, disclaimer, 18+ age-gate and consent modal are
  built and wired in (`LegalAcceptModal`, `LegalDocumentModal`, `LegalFooter`) ✅
- **Error tracking (Sentry)** — added, opt-in via `SENTRY_DSN` / `VITE_SENTRY_DSN` ✅ *(2026-07-18)*

**Not built yet (the gaps):**

- No payment system (Razorpay library is installed, but no tiers, checkout, or webhook yet)
- No real push notifications (current alerts only fire while the app is open)
- No **Refund / Cancellation** policy page (needed before charging money, Phase C)

---

## Guiding principle

> **Launch free first. Learn what people love. Then charge for it.**

Charging before we know what users value is guessing at price and packaging.
The free launch is our research.

---

## Phase A — Go live, free (now → ~2 weeks)

**Goal:** get real users, measure what they actually use.

| Task | Status | Why |
|------|--------|-----|
| Add **Sentry** (error tracking) | ✅ Done (set `SENTRY_DSN` on Render, `VITE_SENTRY_DSN` on Vercel to turn on) | So we see crashes/errors in real time |
| **Terms / Privacy** pages | ✅ Already built | Trust + needed later for payments |
| Keep free daily AI limits as-is | ✅ In place | Controls cost while we learn |
| Confirm production is stable (backend + frontend deployed, latest commit) | ⏳ To verify | Baseline |
| Watch analytics: sign-ups, return visits, top features | ⏳ Ongoing | This decides what becomes "Pro" |

**To turn Sentry on:** create a free project at sentry.io, then set the DSN env var
on each host (`SENTRY_DSN` on Render, `VITE_SENTRY_DSN` on Vercel). With no DSN set,
the code is a harmless no-op — nothing breaks.

**Exit criteria:** app is stable, we have 2–4 weeks of usage data, and we can name
the 1–3 features people come back for.

---

## Phase B — Push notifications (the retention hook)

**Goal:** bring people back daily with alerts that arrive **even when the app is closed.**

The valuable alerts already have the data behind them (panchangam cache + personal
Moon tables). Today they only fire while the app is open — that's the thing to fix.

| Task | Why |
|------|-----|
| Add **OneSignal** web push (fastest path) | Alerts when app is closed |
| Server-side scheduler: compute each user's **next ~90 days** of Rahu Kalam / Chandra Ashtama / Tara windows | So alerts can be scheduled ahead |
| Notification preferences UI (already partly exists) | Let users choose what they get |

**Why this before payments:** daily-return alerts are exactly the kind of feature
people will pay for — build the hook, then sell it.

---

## Phase C — Payments & subscription tiers (make money)

**Goal:** turn engaged free users into paying users.

| Task | Why |
|------|-----|
| Add **`subscription_tier`** + status + renewal date to the database | Track who's paid |
| Integrate **Razorpay** (India: UPI, cards, netbanking) | Take payments |
| Backend **billing webhook** (verify payment → update tier) | Keep tiers accurate |
| **Refund / Cancellation** policy page | Razorpay requires it |
| Feature + quota gating by tier | Free vs Pro difference |
| Pricing page + "Manage subscription" screen | The buying experience |

**Suggested free vs Pro split (starting point):**

- **Free:** chart, basic dasha, panchangam, limited chat (daily cap)
- **Pro:** Life Cycle 10-year planner, unlimited chat, push alerts, Prashna, PDF reports

*(Prices to be set after Phase A tells us what people value.)*

---

## Phase D — Premium content (higher-value paid extras)

**Goal:** things worth a one-time or higher price.

| Idea | Notes |
|------|-------|
| **PDF reports** (life reading, career, Life Cycle) | Downloadable, shareable |
| **5-year panchangam almanac** | We already have the generator — just extend 2 → 5 years and import |
| Personalized yearly forecast | Recurring "annual reading" |

---

## Quick reference — the two biggest builds

1. **Push notifications** (Phase B) → daily retention
2. **Payments + tiers** (Phase C) → revenue

Everything else is either done, small, or a bonus.

---

## Housekeeping (do alongside)

- Commit the still-untracked **MA-exam files** and `scripts/` (or decide to keep them out)
- Tidy database migrations (SQL files are currently loose in `supabase/`)
- Confirm CORS / secrets / API keys are set on production for every new feature
