# Features — Technical Reference

Per-feature implementation guide for **debugging**, **production incidents**, and **onboarding engineers**.  
Companion to [DEVELOPER-GUIDE.md](./DEVELOPER-GUIDE.md).

**Last updated:** 2026-07-12 (Life Cycle Simulator Phase 1–3, SW `life-cycle` tab)

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
12. [Ashtakavarga & AV triggers](#12-ashtakavarga--av-triggers)
13. [My Chart sub-panels](#13-my-chart-sub-panels)
14. [Life Cycle Simulator](#14-life-cycle-simulator)
15. [Service worker & PWA](#15-service-worker--pwa)
16. [Production troubleshooting matrix](#16-production-troubleshooting-matrix)

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
| Ashtakavarga | My Chart section | `POST /ashtakavarga` | `ashtakavarga_agent` | No | SAV only in prompt |
| AV triggers | Home + Ashtakavarga | `POST /ashtakavarga/triggers` | `compute_trigger_status()` | No | — |
| Prashna | Prashna tab | `POST /prashna/analyze` | `prashna/*` | Optional | — |
| Life Cycle | Life Cycle tab (`?tab=life-cycle`) | `POST /prediction/simulate` | `prediction_simulator/*` | Optional | — |
| Panchangam | Panchangam tab | `GET /panchangam/*` | `panchangam_agent` | No | 📅 |
| Personal Panchangam | Home card | `GET /personal-panchangam/*` + triggers | `tara_engine`, `ashtama_agent`, `ashtakavarga_agent` | No | ⭐ |

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

Chip **🔗 House Links** → `house_connections_context_for_narrator(natal_chart, user_message)`:

| Mode | When | Prompt size |
|------|------|-------------|
| **Compact** (default) | General chat | One line per house (strength + top channel) |
| **Detail** | User asks about House Links, channels, or a specific house (e.g. "Explain H9") | Full per-house cards with Channels IN/OUT, blessers, HOW TO EXPLAIN guide |

**Production note:** Before `c1e399e`, injecting full detail for all 12 houses on every chat request (~31k chars) contributed to `/chat` **503** failures alongside a broken import. Always keep House Links chat context **lazy** — do not revert to unconditional full cards.

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
9. House Links (`house_connections_context_for_narrator(natal_chart, user_message)` — **lazy**: compact by default, detail on demand)

Each block wrapped in try/except — failure is non-fatal.

### House Links lazy context (`house_connections/narrator.py`)

Detail mode triggers when `user_message` matches:

- House Links / channels / prediction map keywords, or
- Specific house references (`H9`, `house 9`, `9th house`, etc.)

Default compact mode: 12 one-line summaries (~2k chars). Detail mode: full cards for requested houses only.

**Do not** inject all 12 full house cards on every request — caused production 503s (oversized system prompt) before `c1e399e`.

### Chat 503 errors (production)

| HTTP detail | Cause | Fix |
|-------------|-------|-----|
| `OpenAI rate limit. Try again in a minute.` | OpenAI quota / RPM | Wait; check OpenAI dashboard |
| `OpenAI API key is invalid...` | Missing/wrong `OPENAI_API_KEY` on Render | Set env var; redeploy |
| `Chat service temporarily unavailable.` | `_build_system` failed (import/chart) or uncategorized RuntimeError | Render logs → `[chat_agent]` / `Chat RuntimeError` |
| Generic 500 | Unhandled exception in OpenAI call | Render traceback |

Probe:

```bash
curl -s -X POST "$API/chat" -H 'Content-Type: application/json' \
  -d '{"natal_chart":{...},"messages":[{"role":"user","content":"Hello"}]}' | jq .
```

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

## 12. Ashtakavarga & AV triggers

### Purpose

**BAV/SAV** — bindu scores per sign/house (Tamil rules, ported from [Ashtavargam](https://github.com/sivaramanrajagopal/Ashtavargam)). Used for Gochara transit scoring (SAV house-wise) and My Chart grids.

**Shodhya Pinda triggers** — advanced reduction (Trikona + Ekadhipatya Shodhana) → one strength number per planet. `Shodhya Pinda % 27` maps to a **trigger nakshatra**. When **Moon transits** that nakshatra, that planet's significations tend to manifest more visibly (classical Ashtakavarga timing).

### Files

```
backend/agents/ashtakavarga_agent.py     # BAV/SAV, Shodhya Pinda, compute_trigger_status()
frontend/src/components/AshtakavargaPanel.jsx
frontend/src/components/AvTriggerCard.jsx
frontend/src/components/PersonalPanchangamCard.jsx   # compact trigger banner
backend/tests/test_ashtakavarga_triggers.py
```

### APIs

```
POST /ashtakavarga
  → bav, sav, matrix_8x8, trigger_status (today's Moon match + next trigger)

POST /ashtakavarga/triggers
  → lightweight trigger_status only (used by Personal Panchangam card)
  Query: ?date=YYYY-MM-DD (optional)
  Rate: 60/min
```

### `trigger_status` response (key fields)

| Field | Description |
|-------|-------------|
| `today_moon_nak` | Moon nakshatra on evaluation date (noon local) |
| `is_trigger_day` | Moon matches ≥1 planet trigger |
| `active_planets[]` | `{planet, shodhya_pinda, pinda_category, houses_ruled, theme}` |
| `hotspots[]` | Nakshatras shared by 2+ planets (`is_triple_trigger` when ≥3) |
| `next_trigger` | `{nakshatra, days_until, date, planets, is_hotspot}` |
| `all_triggers[]` | Full 7-planet trigger list (Ashtakavarga tab expandable) |

### UI placement

| Location | Mode | Content |
|----------|------|---------|
| **Home** — Personal Panchangam card | Compact | Active today **or** "Next AV trigger in X days" |
| **My Chart** — Ashtakavarga tab | Full | Trigger card + collapsible all-planet list |

**Not integrated into:** Gochara scoring (SAV only), House Links, chat prompt (by design — keeps chat lean).

### Mobile

- Stacked planet rows, flex-wrap headers
- `@media (max-width: 639px)` — reduced padding, 44px tap target on `<details>` summary
- Parallel fetch: Panchangam + triggers (`Promise.all`); trigger failure is non-fatal

### Canonical test chart

**1978-09-18 17:35 Chennai** — triple hotspot **Hasta** (Mars + Mercury + Jupiter).

### Tests

```bash
cd backend && python3 -m pytest tests/test_ashtakavarga_triggers.py -q
```

---

## 13. My Chart sub-panels

All on **My Chart** tab (`chart`), lazy-enabled when tab active:

| Section | Component | API |
|---------|-----------|-----|
| D1 + D9 charts | `SouthIndianChart` | from stored chart |
| Dasha roadmap | `DashaRoadmap`, `DashaSummaryCard` | chart JSON |
| Ashtakavarga | `AshtakavargaPanel` + `AvTriggerCard` | `POST /ashtakavarga` (includes `trigger_status`) |
| Tamil Doshas | `TamilDoshasPanel` | `POST /tamil-doshas` → link to Dosha Radar |
| Indu Lagna | `InduLagnaPanel` | `POST /indu-lagna` |

Deep-link scroll: `?tab=chart&section=ashtakavarga` (see `Home.jsx` scroll effect).

---

## 14. Life Cycle Simulator

### Purpose

Forward **10-year Parasara planner**: natal Bhava strength + **SAV** + Drishti + D9 overlay → Vimshottari **MD / AD / PD** → slow-planet Gochara on house lords & karakas → theme-specific activation windows (marriage, career, health, property, foreign, education).

**Method (exam-aligned):** Bhava → SAV → Dasa permission (MD→AD→PD) → Gochara trigger.  
Windows are **indications**, not guaranteed events.

### Files

```
backend/agents/prediction_simulator/
  __init__.py
  agent.py              # compute_life_cycle_simulation (orchestrator)
  constants.py          # LIFE_THEMES, KARAKA_ROLES, PLANET_WEIGHT
  themes.py             # SAV natal promise, PD peaks, verdict + has_caution
  narration.py          # short rule-based headline / theme lines
  ai_narrator.py        # optional 3-sentence OpenAI narration
backend/dasha_core.py   # generate_pratyantars() — PD within each AD
backend/main.py         # POST /prediction/simulate
frontend/src/components/LifeCycleSimulatorPanel.jsx
frontend/src/pages/Home.jsx          # tab key: life-cycle
frontend/src/constants/brand.js      # Life Cycle feature chip
frontend/src/index.css               # .lcs-* mobile styles
backend/tests/test_prediction_simulator.py
```

### API

```
POST /prediction/simulate
Rate limit: 30/minute
Auth: optional JWT (resolve_natal_chart)

Body:
{
  "natal_chart": { ... },   // omit when signed-in + saved chart
  "horizon_years": 10,      // clamped 1–15
  "start_date": null,       // optional ISO date; default = today
  "include_ai": false,      // optional short AI narration
  "language": "english"     // or "tamil" for AI
}
```

**AI path:** If `include_ai=true`:
1. Requires `OPENAI_API_KEY` on Render → else **503** `"OPENAI_API_KEY is not configured."`
2. Then `check_ai_quota(..., "forecast", ...)` (same bucket as daily reading)
3. If OpenAI fails after quota check → response still returns rule-based data; `meta.ai_error` set

### Response shape (key fields)

```json
{
  "meta": {
    "phase": 3,
    "lagna": "Aquarius",
    "navamsa_lagna": "Aries",
    "moon_sign": "Pisces",
    "start_date": "2026-07-12",
    "end_date": "2036-07-11",
    "method": "Parasara: Bhava → SAV → …",
    "ai_narration": false,
    "ai_error": null
  },
  "current_period": {
    "mahadasha": "Moon", "antardasha": "Ketu", "pratyantar": "Venus",
    "pratyantar_start": "...", "pratyantar_end": "...",
    "focus_houses": [2, 6], "life_themes": ["..."]
  },
  "dasha_timeline": [ /* AD segments */ ],
  "pratyantar_timeline": [ /* PD segments over horizon */ ],
  "transit_hits": [ /* Jupiter/Saturn/Mars/Rahu per-sign windows */ ],
  "top_windows": [ /* AD × transit overlaps ranked */ ],
  "caution_windows": [ /* Saturn/Rahu/Mars overlaps */ ],
  "impact_areas": [ /* 12 houses + drishti + strength */ ],
  "event_themes": [
    {
      "key": "health",
      "verdict": "highly_active",
      "has_caution": true,
      "natal_promise_score": 39.2,
      "activation_score": 100,
      "sav": { "average": 24.7, "label": "Average", "by_house": [...] },
      "peak_window": { "type": "overlap|pratyantar|...", "theme_houses": [6,8,12], ... },
      "pratyantar_windows": [ /* top PD clusters for this theme */ ],
      "d9_overlay": { "house_lords": [...], "d9_support": "neutral" }
    }
  ],
  "narration": { "headline": "...", "current_period": "...", "theme_summaries": [...], "caution": "..." },
  "ai_reading": null
}
```

### Scoring notes (production-critical)

| Piece | Rule |
|-------|------|
| Transit scan | **Per sign** — never pass all 12 signs as one target set (that bug spanned full horizon) |
| Theme peak | Must hit **theme houses / lords / karakas** (`themes.py` relevance ≥ 45) |
| Verdict | `highly_active` / `active` / `moderate` / `quiet` from natal + activation + SAV/D9 |
| Caution | Separate flag `has_caution` — does **not** overwrite verdict |
| SAV | Blended into natal promise; labels match Ashtakavarga (≥30 Strong, ≥25 Good, ≥20 Average) |
| PD | `generate_pratyantars(bhukti)` in `dasha_core.py` — AD years × lord/120 |

### UI (`LifeCycleSimulatorPanel.jsx`)

| Section | Mobile behaviour |
|---------|------------------|
| Rule / AI reading | Short headline; AI = 3 sentences max |
| Theme chips | Horizontal scroll |
| Theme detail | SAV chips + Pratyantar list |
| Dasa | Segment **list** on mobile; bar on desktop |
| Charts | D1 / D9 toggle |
| Transits | **Cards** on mobile; table on desktop |
| Impact areas | Collapsed by default |

Deep link: `?tab=life-cycle`

### Golden test native

| Field | Value |
|-------|--------|
| DOB | 1978-09-18, 17:35, Chennai |
| Lagna | Aquarius |
| Tests | `pytest tests/test_prediction_simulator.py -q` (11 tests) |

### Debug checklist

1. Confirm deploy ≥ commit with Life Cycle (`ba03c0c`+) and SW ≥ `jyotish-shell-v7` with `life-cycle` in `ALLOWED_TABS`
2. `GET /openapi.json` includes `/prediction/simulate`
3. Chart has `birth_data.dob`, `planet_positions.Moon.longitude`, `navamsa_positions`
4. Guest: body must include full `natal_chart`; signed-in: JWT + saved chart
5. AI 503 → check Render `OPENAI_API_KEY`
6. AI button no text → check `meta.ai_error` / OpenAI quota
7. All transit hits spanning ~10 years → old backend without per-sign scan fix
8. Tab blank offline / SW error → bump SW cache; hard refresh

### Useful curl

```bash
# Rule-only (no AI quota)
curl -s -X POST "$API/prediction/simulate" -H 'Content-Type: application/json' \
  -d '{"natal_chart":{...},"horizon_years":10}' \
  | jq '.meta.phase, .narration.headline, .event_themes[0].key, .event_themes[0].sav'

# With AI (needs OPENAI_API_KEY + forecast quota)
curl -s -X POST "$API/prediction/simulate" -H 'Content-Type: application/json' \
  -d '{"natal_chart":{...},"horizon_years":10,"include_ai":true}' \
  | jq '.ai_reading, .meta.ai_error'
```

---

## 15. Service worker & PWA

### File

`frontend/public/sw.js` — registered with cache-bust query from app entry.

### Cache

- Shell: `jyotish-shell-v7`
- Precache: `/`, `/index.html`, `/manifest.json`, icons

### Allowed deep-link tabs

```javascript
ALLOWED_TABS = home, chart, career, health, dosha-radar, house-links, gochar,
  panchangam, chat, forecast, prashna, life-cycle, admin
```

Invalid `?tab=` is stripped on navigation fetch to avoid offline shell errors.

### Known production issue (fixed)

**Error:** `Failed to convert value to 'Response'` on `?tab=health`  
**Cause:** SW fetch handler returned `undefined` for unknown tabs  
**Fix:** `cachedShellResponse()` + `offlineHtmlResponse()` fallbacks; bump cache version after tab additions

### After adding a new tab

1. Add key to `ALLOWED_TABS` in `sw.js`
2. Bump `CACHE_SHELL` version (e.g. `v6` → `v7`)
3. Update SW registration query string in frontend if used
4. Users: hard refresh or clear site data once

---

## 16. Production troubleshooting matrix

| Symptom | Feature | Likely cause | Resolution |
|---------|---------|--------------|------------|
| Tab blank after deploy | Any | Old SW cache | Bump `sw.js` cache (`jyotish-shell-v7`+); hard refresh |
| Life Cycle tab blank / SW error | Life Cycle | `life-cycle` missing from SW | Deploy SW with `life-cycle` in `ALLOWED_TABS`; cache v7+ |
| Life Cycle 404 / 500 | Life Cycle | Old backend | Redeploy Render ≥ Life Cycle commit; check `/prediction/simulate` in OpenAPI |
| Life Cycle 422 / natal required | Life Cycle | Guest without chart body | Enter birth details on Home first; signed-in users need saved chart |
| Life Cycle 500 stale chart | Life Cycle | Missing dasha / old schema | Recalculate chart (`StaleChartBanner`) |
| Transit hits span full 10 years | Life Cycle | Pre-fix scan | Deploy agent with **per-sign** `_scan_transits_in_signs` |
| All themes same peak window | Life Cycle | Old theme peak logic | Deploy `themes.py` with theme-house relevance filter |
| Short AI reading → 503 | Life Cycle | Missing `OPENAI_API_KEY` | Set on Render; redeploy |
| Short AI reading → no text | Life Cycle | OpenAI error after quota | Check Render logs; rule reading still works; `meta.ai_error` |
| AI reading 429 | Life Cycle | Forecast AI quota | Same as daily reading limits; wait UTC day or raise env |
| CORS on Life Cycle | All API | `ALLOWED_ORIGINS` | Add exact Vercel origin on Render |
| Chat 503 every message | Chat | Broken import or oversized House Links prompt | Deploy ≥ `c1e399e`; verify lazy `house_connections_context_for_narrator` |
| Chat 503 rate limit | Chat | OpenAI RPM/quota | Wait 1 min; check OpenAI dashboard |
| Chat 503 API key | Chat | `OPENAI_API_KEY` missing/invalid on Render | Set env; redeploy backend |
| AV trigger card missing | Home / Ashtakavarga | Old backend | Deploy ≥ `c6797ec`; `POST /ashtakavarga/triggers` |
| AV trigger card missing (Home only) | Personal Panchangam | Trigger API failed silently | Check Render logs; Panchangam still shows; verify chart + auth |
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
| Chat ignores House Links detail | Chat | Generic question | Ask "Explain H9" or use 🔗 House Links chip — lazy context |
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

# Life Cycle
curl -s -X POST "$API/prediction/simulate" -H 'Content-Type: application/json' \
  -d '{"natal_chart":{...},"horizon_years":10}' \
  | jq '.meta.phase, .narration.headline, .event_themes[0].sav, (.pratyantar_timeline|length)'

# AV triggers (today)
curl -s -X POST "$API/ashtakavarga/triggers" -H 'Content-Type: application/json' \
  -d '{"natal_chart":{...}}' | jq '.is_trigger_day, .active_planets, .next_trigger'

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
pytest tests/test_ashtakavarga_triggers.py -q
pytest tests/test_house_connections*.py tests/test_dasa_activation.py tests/test_chat_house_connections_context.py -q
pytest tests/test_prediction_simulator.py -q
pytest tests/ -q   # full suite

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
7. Add tab to `ALLOWED_TABS` in `frontend/public/sw.js` and bump `CACHE_SHELL`
8. Optional chip in `ChatPanel.jsx` `TOPICS`
9. `backend/tests/test_my_feature.py` + chat context test
10. Update this doc + DEVELOPER-GUIDE feature index

---

*For architecture, database SQL order, and deployment steps see [DEVELOPER-GUIDE.md](./DEVELOPER-GUIDE.md).*
