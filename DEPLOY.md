# Jyotish AI — Deployment Guide
## GitHub → Render (backend) + Vercel (frontend) — 100% free

---

## PART 1 — GitHub Setup (new repo, safe check-in)

### Step 1: Verify secrets are excluded
Before doing anything, confirm `.gitignore` exists and covers your `.env` files:
```bash
cd "Mundane Astrology/jyotish-ai"
cat .gitignore           # should list .env and .env.*
git status               # .env files must NOT appear as untracked
```
If `.env` files still show up, something is wrong — stop and fix `.gitignore` first.

### Step 2: Create a new GitHub repo
1. Go to https://github.com/new
2. Name it: `jyotish-ai`
3. Set to **Private** (recommended until you're ready to launch)
4. Do NOT initialise with README/gitignore (you already have both)
5. Click **Create repository**

### Step 3: Push the code
```bash
cd "Mundane Astrology/jyotish-ai"

git init                          # only if not already a git repo
git add .                         # stages everything (secrets excluded by .gitignore)
git status                        # REVIEW — confirm no .env files are staged
git commit -m "Initial commit — Jyotish AI v1"

git remote add origin https://github.com/YOUR_USERNAME/jyotish-ai.git
git branch -M main
git push -u origin main
```

### Step 4: Verify on GitHub
Open your repo on GitHub and confirm:
- ✅ `backend/.env` is NOT visible (only `.env.example` should be there)
- ✅ `frontend/.env` is NOT visible
- ✅ No API keys anywhere in the codebase

---

## PART 2 — Deploy Backend to Render (free)

### Step 1: Sign up / log in
Go to https://render.com and sign in with your GitHub account.

### Step 2: New Web Service
1. Click **New → Web Service**
2. Connect your GitHub account if not already done
3. Select the `jyotish-ai` repository
4. Configure:

| Setting | Value |
|---------|-------|
| Name | `jyotish-ai-backend` |
| Root Directory | `backend` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | **Free** |

### Step 3: Set Environment Variables
In Render dashboard → your service → **Environment** tab, add these:

```
SUPABASE_URL          = https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY  = eyJ...your-service-role-key...
OPENAI_API_KEY        = sk-proj-...
ANTHROPIC_API_KEY     = sk-ant-...  (if using Claude narrator)
ALLOWED_ORIGINS       = https://your-frontend.vercel.app  ← update after Step 3 below
APP_ENV               = production
ADMIN_TOKEN           = make-up-a-long-random-secret-string
```

**Do NOT put these in any file — only in the Render dashboard.**

### Step 4: Deploy
Click **Create Web Service**. Render will:
1. Clone your repo
2. Run `pip install -r requirements.txt`
3. Start uvicorn

Your backend URL will be: `https://jyotish-ai-backend.onrender.com`

### Step 5: Test
```bash
curl https://jyotish-ai-backend.onrender.com/ping
# Expected: {"pong": true}

curl "https://jyotish-ai-backend.onrender.com/panchangam/today?location=Chennai"
# Expected: panchangam JSON
```

---

## PART 3 — Deploy Frontend to Vercel (free)

### Step 1: Sign up / log in
Go to https://vercel.com and sign in with GitHub.

### Step 2: Import project
1. Click **Add New → Project**
2. Import your `jyotish-ai` repository
3. Configure:

| Setting | Value |
|---------|-------|
| Framework Preset | `Vite` |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

### Step 3: Set Environment Variables
In Vercel → your project → **Settings → Environment Variables**:

```
VITE_API_URL = https://jyotish-ai-backend.onrender.com
```

### Step 4: Deploy
Click **Deploy**. Your frontend URL will be: `https://jyotish-ai.vercel.app`

### Step 5: Update ALLOWED_ORIGINS on Render
Go back to Render → your backend → Environment:
```
ALLOWED_ORIGINS = https://jyotish-ai.vercel.app
```
Click **Save** — Render will redeploy automatically.

---

## PART 4 — Render Keep-Alive (already implemented in code)

The frontend already pings `GET /ping` every 9 minutes via `useKeepAlive()` in `Home.jsx`.
This keeps the Render free instance warm and avoids the 50-second cold start when a user opens the app.

**How it works:**
- On first page load → immediately pings `/ping`
- Every 9 minutes → pings again (Render sleeps after 15 min of inactivity)
- Zero cost: the `/ping` endpoint returns `{"pong":true}` — no DB or AI calls

---

## PART 5 — Custom Domain (optional, free)

### On Vercel (frontend)
1. Vercel dashboard → your project → **Settings → Domains**
2. Add your domain (e.g. `jyotish.ai`)
3. Follow CNAME/A-record instructions for your DNS provider

### On Render (backend)
1. Render dashboard → your service → **Settings → Custom Domain**
2. Add `api.jyotish.ai`
3. Then update `ALLOWED_ORIGINS` on Render to `https://jyotish.ai`

---

## PART 6 — Ongoing deployments

Every time you push to `main` on GitHub:
- Render auto-deploys the backend ✅
- Vercel auto-deploys the frontend ✅

To update secrets/env vars, always use the Render/Vercel dashboards — never commit `.env` files.

---

## Security checklist before going live

- [ ] `backend/.env` and `frontend/.env` are NOT committed to GitHub
- [ ] `ALLOWED_ORIGINS` is set to your exact Vercel URL (not `*`)
- [ ] `APP_ENV=production` set on Render (disables /docs and /redoc)
- [ ] `ADMIN_TOKEN` set to a long random string (protects /bulk-preload)
- [ ] Supabase Row Level Security (RLS) enabled on `natal_charts` table
- [ ] OpenAI API key usage limits set at https://platform.openai.com/usage
