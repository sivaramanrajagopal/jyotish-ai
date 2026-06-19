# Features — Technical Reference

Per-feature implementation guide for **debugging**, **production incidents**, and **onboarding engineers**.  
Companion to [DEVELOPER-GUIDE.md](./DEVELOPER-GUIDE.md).

**Last updated:** 2026-06-06 (House Links channels/BB split, Dasa life areas)

---

## Table of contents

1. [Feature index](#1-feature-index)
2. [Career (D1 + D10)](#2-career-d1--d10)
3. [Health (D3 Drekkana)](#3-health-d3-drekkana)
4. [Dosha Radar (obstruction + Pushkara)](#4-dosha-radar-obstruction--pushkara)
5. [Horai & Uba Horai](#5-horai--uba-horai)
6. [House Links (prediction map)](#6-house-links-prediction-map)
7. [Bhavat Bhavam](#7-bhavat-bhavam)
8. [Tamil Doshas](#8-tamil-doshas)
9. [Indu Lagna](#9-indu-lagna)
10. [Gochara / Forecast](#10-gochara--forecast)
11. [Chat AI grounding](#11-chat-ai-grounding)
12. [My Chart sub-panels](#12-my-chart-sub-panels)
13. [Service worker & PWA](#13-service-worker--pwa)
14. [Production troubleshooting matrix](#14-production-troubleshooting-matrix)

---

## 1. Feature index

| Feature | UI location | API | Engine path | LLM? | Chat chip |
|---------|-------------|-----|-------------|------|-----------|
| Natal + Dasha | Home, My Chart | `POST /natal-chart` | `natal_agent`, `dasha_agent` | No | 🔄 📊 🗓 |
| Gochara | Gochar tab | `POST /forecast/scores` | `transit_score_agent` | No | (in prompt) |
| Forecast AI | Forecast tab | `/forecast/*` | scores + OpenAI | Yes | — |
| Career | Career tab | `POST /career/predict` | `career_agent`, `career/*` | No* | 💼 |
| Health | Health tab | `POST /health/analyze` | `health_agent`, `health/*` | No* | 🏥 |
| Dosha Radar | Dosha Radar tab (`?tab=dosha-radar`) | `POST /dosha-radar/analyze` | `dosha_radar_agent`, `dosha_radar/*` | No* | 🔥 |
| Horai & Uba Horai | Panchangam tab (below limbs) | — (client-side) | `frontend/src/lib/horai.js` | No | — |
| House Links | House Links tab | `POST /house-connections/analyze` | `house_connections_agent`, `house_connections/*` | No* | 🔗 |
| Bhavat Bhavam | Career + Health layers | bundled in career/health | `bhavat_bhavam/*` | No | 🏠 |
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

## 4. Dosha Radar (obstruction + Pushkara)

### Purpose

Live **obstruction dosha** scan for timing awareness — ported from Mundane `hora-calculator` / `obstruction_dosha.py` / `natal_protection.py` logic:

- **Tamil blueprint** — Thithi Soonya signs, Chandrashtama, Mudakku (22nd Drekkana), Vadhai/Vainasikam red-zone nakshatras (reuses `tamil_dosha_agent`)
- **Natal afflictions** — combustion, Gandanta, Pushkara Navamsa, critical obstruction (Visha Gati) with **Divine Protection** when Pushkara applies
- **Live transit scan** — per-planet flags today (Soonya, Chandrashtama, Mudakku, red zones, Pushkara)
- **90-day forecast** — upcoming obstruction windows
- **180-day Pushkara transit windows** — when planets enter/exit Pushkara zones

**Not** a full Natal Protection score (Tab 7 parity from hora-calculator). **Not** medical or financial advice.

**Discoverability:** `?tab=dosha-radar` · Home hero pill **Dosha Radar** (`brand.js`) · My Chart **Tamil Doshas** section link → Dosha Radar tab.

### Files

```
backend/agents/dosha_radar_agent.py          # orchestrator + dosha_radar_context_for_narrator
backend/agents/dosha_radar/pushkara.py       # 24 Pushkara Navamsa zones + transit scan
backend/agents/dosha_radar/afflictions.py    # combust, gandanta, critical_obstruction
backend/agents/dosha_radar/obstruction.py    # profile, live transit, 90d scan
frontend/src/components/DoshaRadarPanel.jsx
frontend/src/pages/Home.jsx                  # tab + Tamil Doshas deep link
frontend/src/constants/brand.js              # APP_FEATURE_LINKS pill
backend/tests/test_dosha_radar.py
backend/tests/test_chat_dosha_radar_context.py
```

### API

```
POST /dosha-radar/analyze
Body: { natal_chart?: object }   // omitted when JWT + saved chart
Auth: optional JWT (resolve_natal_chart)
Rate: 30/min
```

### Response shape (key fields)

```json
{
  "disclaimer": { "en", "ta" },
  "summary": {
    "transit_date", "overall_status", "active_alert_count",
    "natal_pushkara_count", "divine_protection_natal",
    "soonya_signs", "chandrashtama_sign", "mudakku_sign",
    "vadhai_nakshatra", "vainasikam_nakshatra",
    "forecast_horizon_days", "transit_highlight_count"
  },
  "tamil_blueprint": { "thithi_soonyam", "mudakku", "yogi", ... },
  "obstruction_profile": { "soonya_rasis", "soonya_signs", "mudakku", ... },
  "natal_afflictions": {
    "Mercury": {
      "combust", "gandanta", "pushkara", "in_soonya", "critical_obstruction"
    }
  },
  "pushkara_natal": [{ "planet", "pushkara", "zone" }],
  "transit_status": { "transit_date", "planets": { ... } },
  "active_alerts": [{ "planet", "severity", "note_en", "has_divine_protection" }],
  "transit_highlights": [{ "planet", "flags", "has_divine_protection" }],
  "forecast": { "days_ahead": 90, "events": [...] },
  "pushkara_transits": [{ "planet", "currently_pushkara", "next_entry_days", ... }]
}
```

### Severity ranking (alerts)

| Severity | Meaning |
|----------|---------|
| `soonya` | Planet transiting dagdha (void) sign for birth tithi |
| `mild` / `mild_divine` | Combustion or Gandanta obstruction; `_divine` = Pushkara relief |
| `chandrashtama` | Moon in 8th from natal Moon sign |
| `mudakku` | Planet in Mudakku Rasi (22nd Drekkana) |
| `red_zone` | Vadhai or Vainasikam nakshatra transit |
| `critical` / `critical_divine` | Combined harsh affliction (Visha Gati) |

### Pushkara Navamsa

- **24 classical zones** in `pushkara.py` (`_PUSHKARA_ZONES`) — sidereal longitude bands per sign/nakshatra/pada
- `check_pushkara(lon)` → natal or transit flag
- `scan_all_pushkara_transits()` → 180-day entry/exit windows for Sun–Ketu

### UI sections (`DoshaRadarPanel.jsx`)

1. Hero — overall status + bilingual disclaimer  
2. Transit highlight cards (mobile-friendly)  
3. Active alerts  
4. Tamil blueprint summary  
5. Natal afflictions table (combust / Gandanta / Pushkara / critical)  
6. Live transit grid  
7. 90-day forecast (collapsible)  
8. Pushkara transit windows  
9. Primer — “What is Dosha Radar?” (collapsible)

### Chat integration

- Chip **🔥 Dosha Radar** in `ChatPanel.jsx` `TOPICS`
- Auto-detect topic on replies mentioning pushkara, chandrashtama, obstruction dosha, etc.
- `dosha_radar_context_for_narrator()` appended in `chat_agent._build_gochara_block()` (after Bhavam)
- Chat rules in `chat_agent.py` instruct narrator to cite Pushkara / Divine Protection when present

### Relation to Tamil Doshas (My Chart)

| Layer | My Chart `TamilDoshasPanel` | Dosha Radar tab |
|-------|----------------------------|-----------------|
| Natal blueprint | ✅ Full detail + parihara | ✅ Summary + link back |
| Live transits | ❌ | ✅ |
| Pushkara | ❌ | ✅ Natal + transit |
| Forecast | ❌ | ✅ 90d obstruction + 180d Pushkara |

**Mudakku note:** Radar uses **22nd Drekkana** method; My Chart may show Method A/B — both are documented in Tamil Doshas panel.

### Golden test native

`1978-09-18 17:35 Chennai` (`test_dosha_radar.py`):

- Soonya signs: Dhanu, Meena  
- Chandrashtama: Tula  
- Mudakku: Kanni  
- Natal Pushkara: Mercury, Jupiter, Ketu  

### Debug checklist

| Symptom | Check |
|---------|--------|
| Tab empty / 500 | Chart stale → recalculate; verify `birth_data` lat/lon/tz |
| No Pushkara natal | Planet longitudes missing in `planet_positions` |
| Alerts always empty | Ephemeris / server time; check `transit_status.planets` in API JSON |
| Chat ignores Pushkara | Redeploy backend with `dosha_radar_context_for_narrator` wired |
| Tab offline blank | `dosha-radar` in `sw.js` `ALLOWED_TABS`; cache ≥ v4 |

---

## 5. Horai & Uba Horai

### Purpose

Classical **planetary hour** (Horai) calculator inside the **Panchangam** tab — weekday planet sequences, 12 day + 12 night slots, **Uba Horai** (5 sub-divisions per main hora). Ported from [hora-calculator](https://github.com/sivaramanrajagopal/hora-calculator). Uses **Panchangam location timezone** (not device TZ when abroad).

**No backend API** — pure client logic from Panchangam `sunrise` / `sunset` ISO times.

### Files

```
frontend/src/lib/horai.js              # sequences, slot math, midnight rule
frontend/src/lib/horai.test.js         # vitest (10 cases)
frontend/src/components/HoraiPanel.jsx
frontend/src/components/PanchangamTab.jsx   # mounts HoraiPanel below limbs
frontend/src/index.css                 # .hr-* styles
```

### Calculation modes

| Mode | Day anchor | Night span |
|------|------------|------------|
| **Fixed 6 AM** (default) | 06:00–18:00 on calendar date | 18:00 same date → 06:00 next date |
| **Sunrise** | Sunrise–sunset (12 equal slots) | Sunset → next sunrise (12 equal slots) |

Toggle in `HoraiPanel` header. Sunrise mode fetches **next day’s sunrise** via `GET /panchangam/date?date={displayDate+1}`.

### Midnight rule (critical)

Times **before the day anchor** belong to the **previous calendar day’s night horas**:

- **Fixed mode:** `[00:00, 06:00)` → owner date = **previous calendar day** (night slots 18–23 of that day’s sequence)
- **Sunrise mode:** `[00:00, today_sunrise)` → same rule using sunrise instead of 6 AM

**Display date** `D` always shows **D’s weekday** for the planet sequence grid. **Live highlight** only when `live.ownerYmd === displayDate`. Banner + tap jumps to owner date when viewing before anchor.

### Slot index mapping

- Day slots: indices **0–11**  
- Night slots: indices **12–23**  
- `expandPlanetSequence(weekdaySun0)` — 24 planets from Sunday=0 … Saturday=6 base sequence  
- `getUbaPlanet(mainPlanet, minuteInHour)` — 12-minute sub-slots within current hora

### Time label formatting (sunrise mode fix)

Uneven day/night spans produce **fractional minute** boundaries when divided by 12. Labels use `divideSpanMinutes()` (rounded boundaries, pinned endpoints) and `formatMinutesLabel()` (direct wall-clock formatting — **no** `new Date()` parsing). Prevents **Invalid Date** in production.

Before next-sunrise fetch completes, night span estimates `sunriseMin + 24h`.

### UI sections

1. Mode toggle (6 AM / Sunrise) — 44px touch targets  
2. Mismatch banner (before anchor → link to owner date)  
3. **Current horai** — planet, Uba, slot range, countdown  
4. **Day horai** grid (12 cells)  
5. **Night horai** grid — collapsed by default on viewports &lt;640px  
6. Planet activities primer (Tamil tradition)

### Tests

```bash
cd frontend && npm test -- src/lib/horai.test.js
```

Covers midnight rule, owner date, sunrise label regression (no Invalid Date).

### Known gaps

- No dedicated tab or Ask AI chip yet  
- No Home “current horai” compact strip  
- Horai times use Panchangam city TZ, not traveller device TZ (intentional)

---

## 6. House Links (prediction map)

### Purpose

Astrologer **prediction map** for all 12 houses: lord placement from own house, lord↔lord links (conjunction/aspect/mutual), pada lord & sign lord edges, dusthana chains, blesser ranking, Raja/Dharma–Karma yogas, and **Dasa life-area activation** (7-step Maha/Bhukti house sequence). **Bhavat Bhavam** appears only as a **recovery note** on dusthana prediction cards (H6/H8/H12) — not in channel graph or blesser edges. Ported from [Astrology House Connections](https://huggingface.co/spaces/sivaramrb901/Astrology-House-Connections).

### Files

```
backend/agents/house_connections_agent.py
backend/agents/house_connections/core.py      # lords, strength, houses_from_own (owned=1st)
backend/agents/house_connections/edges.py
backend/agents/house_connections/blessers.py
backend/agents/house_connections/yogas.py
backend/agents/house_connections/inference.py   # channels + dusthana BB recovery note
backend/agents/house_connections/dasa_activation.py   # 7-step Maha/Bhukti chain
frontend/src/components/HouseLinksPanel.jsx
frontend/src/components/HouseLinksGraph.jsx
frontend/src/components/SouthIndianChart.jsx          # highlightBhavaHouses prop
backend/tests/test_house_connections.py
backend/tests/test_house_connections_logic.py
backend/tests/test_house_connections_edges.py         # BB excluded from graph
backend/tests/test_dasa_activation.py
backend/tests/test_chat_house_connections_context.py
```

### API

```
POST /house-connections/analyze
Body: { natal_chart?: object }
Rate: 30/min
```

### Response shape (key fields)

| Field | Description |
|-------|-------------|
| `houses[]` | Per-house lord, seat, from-own type, strength, RAG |
| `edges[]` | Lord placement, same-lord, mutual aspect, pada/sign lord, dusthana chain (no Bhavat Bhavam) |
| `yogas[]` | Kendra–Trikona Raja Yoga, Dharma–Karma Adhipati |
| `predictions[]` | Per-house inference, channels in/out, blessers, `recovery_edges` (dusthana BB only) |
| `graph` | SVG node positions + edge list |
| `summary.maha_dasa/bhukti` | Current Vimshottari lords |
| `dasa_life_areas` | Maha + Bhukti activation chains + combined focus/background |

### Lord placement from own (core logic)

Inclusive count from **owned house as 1st** (not 12th):

```python
houses_from_own(house_num, lord_house) = ((lord_house - house_num) % 12) + 1
```

- Lord in owned sign → `hfo=1` → `own_house`
- 12th from own (e.g. H5 lord in H4) → `hfo=12` → `dusthana_from_own` (not own house)

Canonical test chart: **1978-09-18 17:35 Chennai** — H11 Jupiter in H6 = 8th from own (dusthana).

### Dasa life-area activation (7-step chain)

Separate chain for **Mahadasha lord** and **Antardasha (Bhukti) lord**. Combined focus = union of both house sets.

| Step | Key | What activates |
|------|-----|----------------|
| 1 | `dasa_seat` | Dasa planet's D1 house seat |
| 2 | `dasa_nakshatra` | **Natal nakshatra of the running Dasa lord** (Maha or Bhukti planet — not always Moon; not transit nakshatra) → nakshatra lord link |
| 3 | `nak_lord_seat` | Nakshatra lord's D1 seat |
| 4 | `nak_lord_ownership` | Nakshatra lord's owned houses |
| 5 | `occupant_spread` | Planets in houses **ruled by** the Dasa lord → those occupants' owned houses |
| 6 | `dasa_ownership` | Dasa lord's owned houses |
| 7 | `dasa_seat_anchor` | Dasa planet seat again (final anchor) |

**Interpretation:** emphasize **focus** house themes during the period; de-emphasize **background** houses (transits/divisionals still apply).

**Example (Kumbha lagna, Moon MD):** Moon H2, Revati → Mercury H5/H8/H7, Moon rules H6, Jupiter in H6 → H2/H11 → focus **H2, H5, H6, H7, H8, H11**.

### Channels in / Channels out

Computed from **structural natal edges only** (`edges.py` → `inference.py`). Not transits, not Dasa focus houses, **not Bhavat Bhavam**.

| UI label | Code | Meaning |
|----------|------|---------|
| **Channels in** | Supportive edges with `to_house` = focus house | Life areas that **feed into** this house (lord placement, lord links, pada/sign lord, benefic aspect) |
| **Channels out** | Edges with `from_house` = focus house (excluding self) | Life areas this house **channels outward to** |

Edge kinds in the graph: `lord_placement`, `same_lord`, `lord_link`, `mutual_aspect`, `pada_lord`, `pada_lord_placement`, `sign_lord`, `dusthana_chain` (stress), `aspect_on_house`.

**Blesser scores** use the same edge list — BB edges do not add blesser points.

### Bhavat Bhavam vs House Links

| | House Links graph | House Links dusthana card | Career / Health |
|--|-------------------|---------------------------|-----------------|
| BB edges in channels | ❌ | — | — |
| BB recovery note | — | ✅ H6→11, H8→3, H12→11 via `dusthana_recovery_edges()` | Full evaluated links when primary active |
| Chat chip | 🔗 House Links | — | 🏠 Bhavam |

Deploy **`eda3262`** or later for BB exclusion from channels/blessers.

### UI

Tab **🔗 House Links** (`?tab=house-links`):

1. **D1 Rasi reference** — compact `SouthIndianChart`; orange tint on combined Dasa focus bhavas (`highlightBhavaHouses`)
2. **Dasa life areas** — focus/background chips, expandable 7-step sequences (Maha + Bhukti)
3. Circular **HouseLinksGraph**, focus house selector, prediction card
4. Collapsible 12-house grid, lord-link yoga list

Mobile: single-column layout; D1 + Dasa stack above graph; touch-friendly chips (44px targets where applicable).

### Chat

Chip **🔗 House Links** → `house_connections_context_for_narrator()` — per-house cards with Channels IN/OUT edge labels, blessers, stress, and **HOW TO EXPLAIN** guide for chat.

### Tests

```bash
cd backend && python3 -m pytest tests/test_house_connections*.py tests/test_dasa_activation.py tests/test_chat_house_connections_context.py -q
```

---

## 7. Bhavat Bhavam

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

## 8. Tamil Doshas

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

**Link to Dosha Radar:** `TamilDoshasPanel` includes a button → `?tab=dosha-radar` for live transit + Pushkara layer.

### Chat chip

**🔯 Tamil Doshas** — `dosha_context_for_narrator()` in chat prompt.

---

## 9. Indu Lagna

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

## 10. Gochara / Forecast

Unchanged core — see DEVELOPER-GUIDE §8 `transit_score_agent.py`.

**Blend:** 55% natal lord + 35% Gochara from Moon + 10% SAV.

**Gochar tab** = rule-only (`GocharamTab` → `POST /forecast/scores`).  
**Forecast tab** adds AI via `/forecast/daily-reading`, `/forecast/house`.

---

## 11. Chat AI grounding

### System prompt assembly (`chat_agent.py`)

Order appended to base prompt:

1. Gochara compact summary (`score_all_houses`)
2. Ashtakavarga (`bav_context_for_narrator`)
3. Tamil Doshas (`dosha_context_for_narrator`)
4. Indu Lagna (`indu_context_for_narrator`)
5. Career (`career_context_for_narrator`)
6. Health (`health_context_for_narrator`)
7. Bhavat Bhavam (`bhavat_bhavam_context_for_narrator`)
8. Dosha Radar (`dosha_radar_context_for_narrator`)
9. House Links (`house_connections_context_for_narrator`)

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
| 🔥 Dosha Radar | dosha_radar | Obstruction + Pushkara scan |
| 🔗 House Links | house_links | 12-house prediction map |
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

## 12. My Chart sub-panels

All on **My Chart** tab (`chart`), lazy-enabled when tab active:

| Section | Component | API |
|---------|-----------|-----|
| D1 + D9 charts | `SouthIndianChart` | from stored chart |
| Dasha roadmap | `DashaRoadmap`, `DashaSummaryCard` | chart JSON |
| Ashtakavarga | `AshtakavargaPanel` | `POST /ashtakavarga` |
| Tamil Doshas | `TamilDoshasPanel` | `POST /tamil-doshas` → link to Dosha Radar |
| Indu Lagna | `InduLagnaPanel` | `POST /indu-lagna` |

Deep-link scroll: `?tab=chart&section=ashtakavarga` (see `Home.jsx` scroll effect).

---

## 13. Service worker & PWA

### File

`frontend/public/sw.js` — registered with cache-bust query from app entry.

### Cache

- Shell: `jyotish-shell-v6`
- Precache: `/`, `/index.html`, `/manifest.json`, icons

### Allowed deep-link tabs

```javascript
ALLOWED_TABS = home, chart, career, health, dosha-radar, house-links, gochar,
  panchangam, chat, forecast, prashna, admin
```

Invalid `?tab=` is stripped on navigation fetch to avoid offline shell errors.

### Known production issue (fixed)

**Error:** `Failed to convert value to 'Response'` on `?tab=health`  
**Cause:** SW fetch handler returned `undefined` for unknown tabs  
**Fix:** `cachedShellResponse()` + `offlineHtmlResponse()` fallbacks; bump cache version after tab additions

### After adding a new tab

1. Add key to `ALLOWED_TABS` in `sw.js`
2. Bump `CACHE_SHELL` version (e.g. `v4` → `v5`)
3. Update SW registration query string in frontend if used
4. Users: hard refresh or clear site data once

---

## 14. Production troubleshooting matrix

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
| Horai Invalid Date | Horai / Sunrise mode | Old JS bundle | Deploy ≥ `185740d`; bump SW cache; hard refresh |
| Horai wrong “current” before 6 AM | Horai fixed mode | Owner date rule | Expected — banner links to previous calendar day |
| Dosha Radar tab blank offline | Dosha Radar | SW missing tab | `dosha-radar` in `ALLOWED_TABS` |
| House Links tab blank offline | House Links | SW missing tab | `house-links` in `ALLOWED_TABS`; cache v6+ |
| H11 lord “Kendra from own” wrong | House Links | Old from-own count | Deploy ≥ `03b1689`; owned=1st not 12th |
| Dasa focus houses empty | House Links | Missing planet nakshatra | Recalculate chart; verify `planet_positions.*.nakshatra` |
| BB inflating channels in/out | House Links | Old backend | Deploy ≥ `eda3262`; BB is recovery note on H6/H8/H12 only |
| Pushkara missing in chat | Chat | Old backend | `dosha_radar_context_for_narrator` in `chat_agent` |
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

# Dosha Radar
curl -s -X POST "$API/dosha-radar/analyze" -H 'Content-Type: application/json' \
  -d '{"natal_chart":{...}}' | jq '.summary, .pushkara_natal, .active_alerts'

# Health check
curl -s "$API/health" | jq .
```

### Test commands by feature

```bash
cd backend
pytest tests/test_career.py tests/test_chat_career_context.py -q
pytest tests/test_health.py tests/test_chat_health_context.py -q
pytest tests/test_bhavat_bhavam.py tests/test_chat_bhavam_context.py -q
pytest tests/test_dosha_radar.py tests/test_chat_dosha_radar_context.py -q
pytest tests/test_tamil_doshas.py tests/test_indu_lagna.py -q
pytest tests/ -q   # full suite (~95 tests)

cd ../frontend && npm test -- src/lib/horai.test.js
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
