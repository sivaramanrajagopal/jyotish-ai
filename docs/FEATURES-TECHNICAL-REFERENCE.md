# Features — Technical Reference

Per-feature implementation guide for **debugging**, **production incidents**, and **onboarding engineers**.  
Companion to [DEVELOPER-GUIDE.md](./DEVELOPER-GUIDE.md).

**Last updated:** 2026-06-06

---

## Table of contents

1. [Feature index](#1-feature-index)
2. [Career (D1 + D10)](#2-career-d1--d10)
3. [Health (D3 Drekkana)](#3-health-d3-drekkana)
4. [Bhavat Bhavam](#4-bhavat-bhavam)
5. [Tamil Doshas](#5-tamil-doshas)
6. [Indu Lagna](#6-indu-lagna)
7. [Gochara / Forecast](#7-gochara--forecast)
8. [Chat AI grounding](#8-chat-ai-grounding)
9. [My Chart sub-panels](#9-my-chart-sub-panels)
10. [Service worker & PWA](#10-service-worker--pwa)
11. [Production troubleshooting matrix](#11-production-troubleshooting-matrix)

---

## 1. Feature index

| Feature | UI location | API | Engine path | LLM? | Chat chip |
|---------|-------------|-----|-------------|------|-----------|
| Natal + Dasha | Home, My Chart | `POST /natal-chart` | `natal_agent`, `dasha_agent` | No | 🔄 📊 🗓 |
| Gochara | Gochar tab | `POST /forecast/scores` | `transit_score_agent` | No | (in prompt) |
| Forecast AI | Forecast tab | `/forecast/*` | scores + OpenAI | Yes | — |
| Career | Career tab | `POST /career/predict` | `career_agent`, `career/*` | No* | 💼 |
| Health | Health tab | `POST /health/analyze` | `health_agent`, `health/*` | No* | 🏥 |
| Bhavat Bhavam | Career + Health layers | bundled in above | `bhavat_bhavam/*` | No | 🏠 |
| Tamil Doshas | My Chart section | `POST /tamil-doshas` | `tamil_dosha/*` | No | 🔯 |
| Indu Lagna | My Chart section | `POST /indu-lagna` | `indu_lagna_agent` | No | 💰 |
| Ashtakavarga | My Chart section | `POST /ashtakavarga` | `ashtakavarga_agent` | No | (in prompt) |
| Prashna | Prashna tab | `POST /prashna/analyze` | `prashna/*` | Optional | — |
| Panchangam | Panchangam tab | `GET /panchangam/*` | `panchangam_agent` | No | 📅 |
| Personal Panchangam | Home / chart cards | `GET /personal-panchangam/*` | `tara_engine`, `ashtama_agent` | No | ⭐ |

\*Narrator context is injected into chat; tab UI is rule-only.

---

## 2. Career (D1 + D10)

### Purpose

Ten Parashari career rules (PDF10/thesis matrix), D10 Dasamsa chart, profession tags, Vimshottari windows linked to 10th lord / AK / AmK.

### Files

```
backend/agents/career_agent.py          # orchestrator + career_context_for_narrator
backend/agents/career/d10.py            # D10 whole-sign from D1 longitudes
backend/agents/career/rules.py          # 10 rules (evaluate_pdf10_rules)
backend/agents/career/atmakaraka.py     # AK/AmK by degree-in-sign
backend/agents/career/profession.py     # profession tag probabilities
backend/agents/career/timing.py         # Dasa periods touching 10th lord / AK / AmK
frontend/src/components/CareerPanel.jsx
backend/tests/test_career.py
backend/tests/test_chat_career_context.py
```

### API

```
POST /career/predict
Body: { natal_chart?: object, timing_years?: 90 }  // chart omitted when JWT + saved chart
Auth: optional JWT (resolve_natal_chart)
Rate: 30/min
```

### Response shape (key fields)

```json
{
  "summary": {
    "rules_matched", "rules_total", "career_strength",
    "tenth_lord", "tenth_house_sign", "atmakaraka", "amatyakaraka",
    "top_profession", "top_probability"
  },
  "profession_tags": [{ "name", "probability", "reasons" }],
  "rules": [{ "id", "label", "detail", "matched" }],
  "dasamsa_ascendant", "dasamsa_positions",
  "timing": { "current", "upcoming", "all" },
  "bhavat_bhavam": { "slice": "career", "links": [...], "active_count" },
  "hero": { "headline", "career_strength" }
}
```

### Rule engine (10 rules)

| ID | Rule |
|----|------|
| R1 | D1 planets in 10th |
| R2 | D1 10th lord placement |
| R3 | D1 10th lord in 10th |
| R4 | D10 planets in 10th |
| R5 | D10 10th lord strength |
| R6 | D10 Lagna lord strength |
| R7 | Atmakaraka in D10 |
| R8 | Dasha linked to 10th lord |
| R9 | Sun/Mars/Saturn in D10 Kendra |
| R10 | Benefic/malefic balance in D10 Kendra |

**Strength label:** Strong (≥7 rules + high prob), Good, Moderate, Developing.

### D10 calculation

- Built from D1 `longitude` per planet → `build_dasamsa_from_natal()` in `career/d10.py`
- Whole-sign houses from D10 ascendant

### Debug checklist

| Symptom | Check |
|---------|--------|
| 500 on Career tab | Render logs; `birth_data.dob` required for timing |
| 0 rules matched | Verify `ascendant.sign_index` in chart_data |
| D10 chart empty | Recalculate natal chart; check planet longitudes |
| Timing empty | Moon longitude + dob in `birth_data` |
| Bhavam missing | `bhavat_bhavam.links` empty if H10/H2 not active (H10 always active on career slice) |

### Golden test native

`1978-09-18 17:35 Chennai` — expect 6/10 rules in `test_career.py`.

---

## 3. Health (D3 Drekkana)

### Purpose

D3 body-part map (Parasara drekkana decans), awareness factors from D3 houses 6/8/12, active Dasa/Bhukti, slow-planet transits. **Informational only — not medical advice.**

### Files

```
backend/agents/health_agent.py
backend/agents/health/d3.py              # D1 degree → D3 sign (decans)
backend/agents/health/body_map.py      # D3 house + decan → body part EN/TA
backend/agents/health/warnings.py      # scoring, factor_groups, transit_today
frontend/src/components/HealthPanel.jsx
frontend/src/components/BodyMapSvg.jsx
backend/tests/test_health.py
backend/tests/test_chat_health_context.py
```

### API

```
POST /health/analyze
Body: { natal_chart?: object }
Rate: 30/min
```

### Response shape (key fields)

```json
{
  "disclaimer": { "en", "ta" },
  "summary": {
    "overall_risk", "d3_lagna", "maha_dasa", "bhukti", "dasa_period",
    "transit_date", "focus_zone_en", "focus_rationale_en", ...
  },
  "factor_groups": {
    "d3_natal": [{ "planet", "body_part_en", "d3_house", "risk", "tags", "reasons_en", ... }],
    "dasa": [{ "text_en", "text_ta" }],
    "transit": [{ "planet", "house_d1", "house_d3", "text_en", ... }]
  },
  "transit_today": [{ "planet", "sign", "house_d1", "house_d3", "health_sensitive", ... }],
  "body_regions": [{ "zone", "label_en", "score", "risk", "rationale_en", ... }],
  "planet_rows": [{ "planet", "d1_house", "d3_house", "body_part_en", "health_house_d3", ... }],
  "drekkana_ascendant", "drekkana_positions",
  "bhavat_bhavam": { "slice": "health", "links": [...] }
}
```

### Scoring logic (summary)

| Signal | Zone score boost |
|--------|------------------|
| Planet in D3 H6/H8/H12 | +2 |
| Malefic in D3 health house | +2 |
| Active MD/AD lord on row | +2 (d3_natal factor) |
| Slow transit (Sat/Mar/Rahu/Ketu) through D3 health house | +2–2.5 |
| Dasa lord rules health house (6/8/12) | dasa factor text |

**Hero risk** = top `d3_natal` factor risk, else top `body_regions` zone.

### Transit snapshot

- Computed at **today noon** in birth timezone (`health_agent._transit_positions_for_today`)
- Requires `birth_data.lat`, `birth_data.lon`, `birth_data.timezone`

### UI sections (mobile)

1. Today's transits table  
2. 6/8/12 primer (collapsible)  
3. Body map + D3 chart (stacked &lt;768px)  
4. Grouped factors: D3 natal | Dasa | Transit  
5. Bhavat Bhavam layer  
6. Body-part table (collapsed &lt;640px)

### Debug checklist

| Symptom | Check |
|---------|--------|
| Factors show (0) | Backend not deployed; API missing `factor_groups` (pre-7ecfd53) |
| Empty transits | Missing lat/lon in `birth_data` |
| Red head vs “Right knee” lagna | Lagna body = D3 sign mapping; red zone = scored region — see `rationale_en` |
| `duplicate key` in Render logs | `ashtama_agent` upsert — fixed with `on_conflict=user_id,date` |

---

## 4. Bhavat Bhavam

### Purpose

Secondary D1 layer: **house-from-house** support/recovery paths. Does not override D3 or PDF10 scores.

### Formula

Bhavat Bhavam of house **N** = count **N** houses from house **N** (whole-sign, same ascendant).

| Primary | BB house | Theme |
|---------|----------|--------|
| 6 | 11 | Disease → recovery / gains |
| 8 | 3 | Crisis → courage |
| 12 | 11 | Hospital/expense → fulfillment |
| 10 | 7 | Career → partners / public |
| 2 | 3 | Wealth → skills |

### Files

```
backend/agents/bhavat_bhavam/core.py      # evaluate_link, lord aspects
backend/agents/bhavat_bhavam/slices.py    # health + career slices
backend/agents/bhavat_bhavam_agent.py     # narrator + compute_bhavat_bhavam
frontend/src/components/BhavatBhavamLayer.jsx
backend/tests/test_bhavat_bhavam.py
backend/tests/test_chat_bhavam_context.py
```

### Bundled responses

- `compute_health_analysis()` → `bhavat_bhavam` (H6, H8, H12 when active)
- `compute_career_prediction()` → `bhavat_bhavam` (H10 always; H2 when occupied/active dasa)

### Link activation

Shown when `primary_active`:
- Planets in primary house, or
- Primary lord = Mahadasha/Bhukti lord, or
- Career H10 (always on career slice)

### Signal

| Signal | Meaning |
|--------|---------|
| support | BB lord strong / benefic in BB / lords linked / BB lord in dasa |
| watch | Moderate score |
| neutral | Link shown, weak support |

### Chat

- Chip **🏠 Bhavam** in `ChatPanel.jsx`
- `bhavat_bhavam_context_for_narrator()` appended in `chat_agent._build_gochara_block()`

---

## 5. Tamil Doshas

### Purpose

Tamil predictive doshas: Thithi Soonyam, Mudakku A/B, Vadhai/Vainasikam red zones, Yogi/Avayogi.

### Files

```
backend/agents/tamil_dosha_agent.py
backend/agents/tamil_dosha/thithi_soonyam.py
backend/agents/tamil_dosha/mudakku.py
backend/agents/tamil_dosha/red_zones.py
backend/agents/tamil_dosha/yogi.py
frontend/src/components/TamilDoshasPanel.jsx
backend/tests/test_tamil_doshas.py
backend/tests/test_chat_tamil_doshas_context.py
```

### API

```
POST /tamil-doshas
Body: { natal_chart?: object }
```

### UI

Rendered inside **My Chart** tab (`Home.jsx` → `TamilDoshasPanel`), not a separate tab.

### Chat chip

**🔯 Tamil Doshas** — `dosha_context_for_narrator()` in chat prompt.

---

## 6. Indu Lagna

### Purpose

Fortune lagna from Moon + Venus rashis; wealth-favourable Dasa/Bhukti and transit windows.

### Files

```
backend/agents/indu_lagna_agent.py
frontend/src/components/InduLagnaPanel.jsx
backend/tests/test_indu_lagna.py
backend/tests/test_chat_indu_lagna_context.py
```

### API

```
POST /indu-lagna
Body: { natal_chart?: object }
```

### Activation tiers

| Tier | Trigger |
|------|---------|
| primary | Dasa/Bhukti of Indu lord or occupant of Indu sign |
| secondary | Jupiter/Saturn transit over Indu sign or lord's sign |
| minor | Sun/Mercury/Moon through Indu sign |

### Chat chip

**💰 Indu Lagna**

---

## 7. Gochara / Forecast

Unchanged core — see DEVELOPER-GUIDE §8 `transit_score_agent.py`.

**Blend:** 55% natal lord + 35% Gochara from Moon + 10% SAV.

**Gochar tab** = rule-only (`GocharamTab` → `POST /forecast/scores`).  
**Forecast tab** adds AI via `/forecast/daily-reading`, `/forecast/house`.

---

## 8. Chat AI grounding

### System prompt assembly (`chat_agent.py`)

Order appended to base prompt:

1. Gochara compact summary (`score_all_houses`)
2. Ashtakavarga (`bav_context_for_narrator`)
3. Tamil Doshas (`dosha_context_for_narrator`)
4. Indu Lagna (`indu_context_for_narrator`)
5. Career (`career_context_for_narrator`)
6. Health (`health_context_for_narrator`)
7. Bhavat Bhavam (`bhavat_bhavam_context_for_narrator`)

Each block wrapped in try/except — failure is non-fatal.

### Topic chips (`ChatPanel.jsx` → `TOPICS`)

| Chip | key | Pre-filled question |
|------|-----|---------------------|
| 📅 Panchangam | panchangam | Today's Panchangam |
| ⭐ Tara Balam | tara | Good/bad days |
| 🔄 My Dasha | dasha | Current MD/Bhukti |
| 📊 Bhukti Table | dasha_table | Bhukti markdown table |
| 🗓 Dasa Cycle | dasha_cycle | Full MD + bhukti overview |
| 🔯 Tamil Doshas | tamil_doshas | Doshas + parihara |
| 💰 Indu Lagna | indu_lagna | Fortune periods |
| 💼 Career | career | D1+D10 career |
| 🏥 Health | health | D3 awareness |
| 🏠 Bhavam | bhavam | BB recovery paths |
| ✨ Yogas | yoga | Natal yogas |
| 🕐 Muhurta | muhurta | Auspicious timing |
| 🪐 Planets | planets | Influential planet |

### Dasha anti-hallucination

- `refresh_dasha(chart, force=True)` on every `/chat` request
- Markdown tables injected: `bhukti_table_markdown`, `full_dasha_cycle_markdown`
- See DEVELOPER-GUIDE §19

### Quotas

| kind | Routes | Limit env |
|------|--------|-----------|
| chat | `/chat` | `AI_DAILY_CHAT_LIMIT` |
| forecast | `/forecast/*`, prashna AI | `AI_DAILY_FORECAST_LIMIT` |

---

## 9. My Chart sub-panels

All on **My Chart** tab (`chart`), lazy-enabled when tab active:

| Section | Component | API |
|---------|-----------|-----|
| D1 + D9 charts | `SouthIndianChart` | from stored chart |
| Dasha roadmap | `DashaRoadmap`, `DashaSummaryCard` | chart JSON |
| Ashtakavarga | `AshtakavargaPanel` | `POST /ashtakavarga` |
| Tamil Doshas | `TamilDoshasPanel` | `POST /tamil-doshas` |
| Indu Lagna | `InduLagnaPanel` | `POST /indu-lagna` |

Deep-link scroll: `?tab=chart&section=ashtakavarga` (see `Home.jsx` scroll effect).

---

## 10. Service worker & PWA

### File

`frontend/public/sw.js` — registered with cache-bust query `?v=2` from app entry.

### Cache

- Shell: `jyotish-shell-v2`
- Precache: `/`, `/index.html`, `/manifest.json`, icons

### Allowed deep-link tabs

```javascript
ALLOWED_TABS = home, chart, career, health, gochar, panchangam, chat, forecast, prashna, admin
```

Invalid `?tab=` is stripped on navigation fetch to avoid offline shell errors.

### Known production issue (fixed)

**Error:** `Failed to convert value to 'Response'` on `?tab=health`  
**Cause:** SW fetch handler returned `undefined` for unknown tabs  
**Fix:** `cachedShellResponse()` + `offlineHtmlResponse()` fallbacks; bump cache version after tab additions

### After adding a new tab

1. Add key to `ALLOWED_TABS` in `sw.js`
2. Bump `CACHE_SHELL` version (e.g. `v2` → `v3`)
3. Update SW registration query string in frontend
4. Users: hard refresh or clear site data once

---

## 11. Production troubleshooting matrix

| Symptom | Feature | Likely cause | Resolution |
|---------|---------|--------------|------------|
| Tab blank after deploy | Any | Old SW cache | Bump `sw.js` cache version; hard refresh |
| Career/Health 500 | Career/Health | Stale chart schema | `StaleChartBanner` → recalculate chart |
| Career/Health 500 | Career/Health | Missing dob | Ensure `birth_data.dob` in saved chart |
| Health factors (0) | Health | Old API only | Deploy backend ≥ `7ecfd53` |
| Bhavam section missing | Bhavam | No active primary house | Expected for quiet H12; check H6/H8/H10 |
| Chat ignores Career | Chat | Context block failed | Check Render logs `[chat_agent]`; verify chart |
| Chat quota 429 | Chat | `ai_usage` limit | Raise env limit or wait for UTC day roll |
| CORS on Career/Health | All API | `ALLOWED_ORIGINS` | Add exact Vercel origin on Render |
| D10 wrong positions | Career | Tropical vs sidereal | Confirm Lahiri in `ephemeris.py` |
| Transit date wrong | Health | Server UTC vs TZ | Uses birth `timezone` at noon local |
| Ashtama duplicate key | Panchangam | Repeat daily upsert | `on_conflict=user_id,date` in `ashtama_agent` |
| Admin 403 | Admin | Email mismatch | `ADMIN_EMAILS` = `VITE_ADMIN_EMAILS` |
| Analytics 404 | Analytics | Table missing | Run `supabase/analytics_events.sql` |

### Useful curl probes

```bash
# Health (guest — needs full natal_chart in body)
curl -s -X POST "$API/health/analyze" -H 'Content-Type: application/json' \
  -d '{"natal_chart":{...}}' | jq '.factor_groups, .bhavat_bhavam.active_count'

# Career
curl -s -X POST "$API/career/predict" -H 'Content-Type: application/json' \
  -d '{"natal_chart":{...}}' | jq '.summary.rules_matched, .bhavat_bhavam'

# Health check
curl -s "$API/health" | jq .
```

### Test commands by feature

```bash
cd backend
pytest tests/test_career.py tests/test_chat_career_context.py -q
pytest tests/test_health.py tests/test_chat_health_context.py -q
pytest tests/test_bhavat_bhavam.py tests/test_chat_bhavam_context.py -q
pytest tests/test_tamil_doshas.py tests/test_indu_lagna.py -q
pytest tests/ -q   # full suite (~90 tests)
```

---

## Adding a new analysis feature (checklist)

1. `backend/agents/my_feature_agent.py` — pure functions, no OpenAI in core
2. `POST /my-feature` in `main.py` — `resolve_natal_chart`, `assert_chart_not_stale`, rate limit
3. `my_feature_context_for_narrator()` — compact text for chat
4. Wire in `chat_agent._build_gochara_block()` (try/except)
5. `frontend/src/components/MyFeaturePanel.jsx` — `chartPayload(chart, userId)`
6. Tab or sub-panel in `Home.jsx` + `enabled={activeTab === '...'}` pattern
7. Optional chip in `ChatPanel.jsx` `TOPICS`
8. `backend/tests/test_my_feature.py` + chat context test
9. Update this doc + DEVELOPER-GUIDE feature index

---

*For architecture, database SQL order, and deployment steps see [DEVELOPER-GUIDE.md](./DEVELOPER-GUIDE.md).*
