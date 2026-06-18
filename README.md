# Parashara Jyotish (jyotish-ai)

Vedic astrology web app — sidereal natal chart, Gochara, Dasha, Career (D10), Health (D3), Dosha Radar (Pushkara + obstruction doshas), Horai, Prashna, and AI chat grounded in rule engines.

## Quick start (local)

```bash
git clone https://github.com/sivaramanrajagopal/jyotish-ai.git
cd jyotish-ai

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
# Fill Supabase + OpenAI keys (see docs/DEVELOPER-GUIDE.md §6)

# Terminal 1 — API
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 — UI
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173** · API docs **http://localhost:8000/docs**

## Documentation

| Doc | Purpose |
|-----|---------|
| [docs/DEVELOPER-GUIDE.md](docs/DEVELOPER-GUIDE.md) | Architecture, DB, API, deploy, debugging playbook |
| [docs/FEATURES-TECHNICAL-REFERENCE.md](docs/FEATURES-TECHNICAL-REFERENCE.md) | Per-feature implementation (Career, Health, Dosha Radar, Horai, Bhavam, etc.) |
| [docs/STEP-1-PRODUCTION-CONFIG.md](docs/STEP-1-PRODUCTION-CONFIG.md) | Production env checklist |
| [docs/SUPABASE-ANALYTICS-DASHBOARD.md](docs/SUPABASE-ANALYTICS-DASHBOARD.md) | Analytics SQL + admin views |
| [SECURITY.md](SECURITY.md) | Secrets and OWASP notes |

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React 19, Vite, Tailwind → **Vercel** (`frontend/`) |
| Backend | FastAPI, pyswisseph → **Render** (`backend/`) |
| DB / Auth | Supabase PostgreSQL + magic link JWT |

## Tests

```bash
cd backend && pytest tests/ -q
cd frontend && npm run build && npm test
```

CI runs on every push to `main` (`.github/workflows/ci.yml`).

## Production URLs

Set `VITE_API_URL` on Vercel to your Render backend. Set `ALLOWED_ORIGINS` on Render to your Vercel URL. See [DEVELOPER-GUIDE.md §14](docs/DEVELOPER-GUIDE.md#14-deployment).
