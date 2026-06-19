/**
 * HouseLinksPanel — astrologer prediction map: 12-house lord links, blessers, yogas.
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'
import HouseLinksGraph from './HouseLinksGraph'
import SouthIndianChart from './SouthIndianChart'

const RAG_CLASS = {
  strong: 'hl-rag--strong',
  moderate: 'hl-rag--moderate',
  weak: 'hl-rag--weak',
}

function Bilingual({ en, ta, inline = false }) {
  if (inline) {
    return (
      <span>
        <span className="hl-bi__en">{en}</span>
        {ta && <span className="hl-bi__ta"> · {ta}</span>}
      </span>
    )
  }
  return (
    <span>
      <span className="hl-bi__en">{en}</span>
      {ta && <span className="hl-bi__ta">{ta}</span>}
    </span>
  )
}

function PredictionCard({ pred, houseRow }) {
  if (!pred) return null
  const st = pred.structure || {}
  const rag = st.rag || {}
  const top = pred.top_blesser

  return (
    <article className="hl-pred">
      <header className="hl-pred__head">
        <h3 className="hl-pred__title">
          H{pred.house} · <Bilingual en={pred.theme_en} ta={pred.theme_ta} inline />
        </h3>
        <span className={`hl-rag ${RAG_CLASS[rag.status] || ''}`}>
          {rag.emoji} {rag.label_en} ({st.strength}/100)
        </span>
      </header>

      <div className="hl-pred__grid">
        <div>
          <span className="hl-pred__label">Lord</span>
          <strong>{st.lord}</strong> in H{st.lord_house}
        </div>
        <div>
          <span className="hl-pred__label">From own</span>
          {houseRow?.position_en || st.position_type}
        </div>
        <div>
          <span className="hl-pred__label">Channels in</span>
          {(pred.channels_in || []).map(h => `H${h}`).join(', ') || '—'}
        </div>
        <div>
          <span className="hl-pred__label">Channels out</span>
          {(pred.channels_out || []).map(h => `H${h}`).join(', ') || '—'}
        </div>
      </div>

      {top && (
        <div className="hl-pred__blesser">
          <span className="hl-pred__label">Primary blesser</span>
          <strong>{top.planet}</strong>
          <span className="hl-pred__score"> score {top.score}</span>
          {(top.active_maha || top.active_bhukti) && (
            <span className="hl-pred__active"> ● Active in Dasa</span>
          )}
        </div>
      )}

      {(pred.blessers || []).length > 1 && (
        <ul className="hl-blesser-list">
          {pred.blessers.slice(0, 4).map(b => (
            <li key={b.planet} className={b.active_maha || b.active_bhukti ? 'hl-blesser-list__on' : ''}>
              {b.planet} ({b.score})
            </li>
          ))}
        </ul>
      )}

      <p className="hl-pred__inference">{pred.inference_en}</p>
      {pred.inference_ta && <p className="hl-pred__inference hl-pred__inference--ta">{pred.inference_ta}</p>}

      {(pred.incoming_edges || []).length > 0 && (
        <details className="hl-edges">
          <summary>Connection details ({pred.incoming_edges.length})</summary>
          <ul>
            {pred.incoming_edges.map(e => (
              <li key={e.id} className={e.supportive === false ? 'hl-edges__stress' : ''}>
                {e.label_en}
              </li>
            ))}
          </ul>
        </details>
      )}
    </article>
  )
}

function YogaList({ yogas }) {
  if (!yogas?.length) {
    return <p className="hl-muted">No major kendra–trikona or dharma–karma lord yogas flagged.</p>
  }
  return (
    <ul className="hl-yoga-list">
      {yogas.map((y, i) => (
        <li key={`${y.name}-${i}`} className="hl-yoga-list__item">
          <strong>{y.name}</strong>
          <span className="hl-yoga-list__ta">{y.name_ta}</span>
          <p>{y.detail_en}</p>
          <span className="hl-yoga-list__meta">H{y.houses?.join('–H')} · strength {y.strength}</span>
        </li>
      ))}
    </ul>
  )
}

function ActivationChain({ chain, defaultOpen = false, onSelectHouse }) {
  if (!chain?.steps?.length) return null
  return (
    <details className="hl-dasa-chain" open={defaultOpen}>
      <summary className="hl-dasa-chain__summary">
        {chain.period_en}: <strong>{chain.planet}</strong>
        {' · '}
        focus {chain.focus_houses?.map(h => `H${h}`).join(', ')}
      </summary>
      <ol className="hl-dasa-steps">
        {chain.steps.map(step => (
          <li key={step.key} className="hl-dasa-step">
            <span className="hl-dasa-step__num">{step.step}</span>
            <span className="hl-dasa-step__label">
              <Bilingual en={step.label_en} ta={step.label_ta} inline />
            </span>
            <p className="hl-dasa-step__detail">{step.detail_en}</p>
            {step.detail_ta && (
              <p className="hl-dasa-step__detail hl-pred__inference--ta">{step.detail_ta}</p>
            )}
            <div className="hl-dasa-step__houses">
              {(step.houses_added?.length ? step.houses_added : step.houses_all)?.length ? (
                (step.houses_added?.length ? step.houses_added : step.houses_all).map(h => (
                  <button
                    key={`${step.key}-${h}`}
                    type="button"
                    className="hl-dasa-step__house"
                    onClick={() => onSelectHouse?.(h)}
                  >
                    H{h}
                  </button>
                ))
              ) : (
                <span className="hl-dasa-step__house hl-dasa-step__house--none">link only</span>
              )}
            </div>
          </li>
        ))}
      </ol>
    </details>
  )
}

function DasaLifeAreas({ dasa, focusHouse, onSelectHouse }) {
  if (!dasa?.combined) return null
  const combined = dasa.combined

  return (
    <div className="hl-dasa-focus">
      <header className="hl-dasa-section__head" style={{ margin: '0 0 0.65rem', borderRadius: '0.35rem' }}>
        <h3 className="hl-dasa-section__title">
          <Bilingual en="Dasa life areas" ta="தசை வாழ்க்கை துறைகள்" inline />
        </h3>
        <p className="hl-dasa-section__sub">
          {dasa.maha_dasa} Mahadasha · {dasa.bhukti} Bhukti — emphasize focus houses; de-emphasize background
        </p>
      </header>

      <p className="hl-dasa-guidance">{combined.guidance_en}</p>
      {combined.guidance_ta && (
        <p className="hl-dasa-guidance hl-pred__inference--ta">{combined.guidance_ta}</p>
      )}

      <div className="hl-dasa-chip-row" role="list" aria-label="Focus houses">
        {(combined.focus_themes || []).map(t => (
          <button
            key={`f-${t.house}`}
            type="button"
            role="listitem"
            className={`hl-dasa-chip hl-dasa-chip--focus${focusHouse === t.house ? ' hl-house-card--focus' : ''}`}
            onClick={() => onSelectHouse(t.house)}
          >
            H{t.house} {t.theme_en}
          </button>
        ))}
      </div>

      <div className="hl-dasa-chip-row" role="list" aria-label="Background houses">
        {(combined.background_themes || []).map(t => (
          <span key={`b-${t.house}`} role="listitem" className="hl-dasa-chip hl-dasa-chip--bg">
            H{t.house}
          </span>
        ))}
      </div>

      <ActivationChain chain={dasa.mahadasha} defaultOpen onSelectHouse={onSelectHouse} />
      <ActivationChain chain={dasa.antardasha} onSelectHouse={onSelectHouse} />
    </div>
  )
}

function D1ReferenceChart({ chart, focusHouses }) {
  if (!chart?.planet_positions) return null
  const bd = chart.birth_data || {}
  return (
    <div className="hl-dasa-chart-wrap">
      <SouthIndianChart
        title="D1"
        subtitle={`${bd.dob || ''} · ${bd.tob || ''}`}
        planetPositions={chart.planet_positions}
        lagnaSignIndex={chart.ascendant?.sign_index ?? 0}
        variant="classic"
        showDetails={false}
        chartKind="natal"
        highlightBhavaHouses={focusHouses}
      />
      <div className="hl-dasa-chart-legend">
        <span>
          <span className="hl-dasa-chart-legend__dot hl-dasa-chart-legend__dot--active" />
          Active Dasa houses
        </span>
        <span>Lagna ↑ highlighted separately</span>
      </div>
    </div>
  )
}

export default function HouseLinksPanel({ chart, userId, enabled = true }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [focusHouse, setFocusHouse] = useState(10)

  const load = useCallback(() => {
    if (!chart || !enabled) return
    setLoading(true)
    setError('')
    api.post('/house-connections/analyze', chartPayload(chart, userId))
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Could not load House Links.'))
      .finally(() => setLoading(false))
  }, [chart, userId, enabled])

  useEffect(() => {
    if (enabled && chart) load()
  }, [enabled, chart, load])

  const houseMap = useMemo(() => {
    const m = {}
    for (const h of data?.houses || []) m[h.house] = h
    return m
  }, [data])

  const focusPred = useMemo(
    () => (data?.predictions || []).find(p => p.house === focusHouse),
    [data, focusHouse],
  )

  const dasaFocusHouses = useMemo(
    () => data?.dasa_life_areas?.combined?.focus_houses || [],
    [data],
  )

  if (!chart) {
    return <div className="hl-panel hl-panel--muted">Open My Chart first…</div>
  }
  if (loading && !data) return <div className="hl-loading">Building house map…</div>
  if (error) return <div className="hl-error" role="alert">{error}</div>
  if (!data) return null

  const s = data.summary || {}

  return (
    <div className="hl-panel" id="house-links-panel">
      {data.disclaimer?.en && (
        <div className="hl-disclaimer" role="note">
          <strong>{data.disclaimer.en}</strong>
          <p>{data.disclaimer.ta}</p>
        </div>
      )}

      <header className="hl-hero">
        <h2 className="hl-hero__title">
          <Bilingual en="House Links" ta="வீட்டு தொடர்பு வரைபடம்" inline />
        </h2>
        <p className="hl-hero__meta">
          {s.edge_count} connections · {s.yoga_count} yogas · Dasa {s.maha_dasa}–{s.bhukti}
        </p>
        <div className="hl-hero__chips">
          {(s.strongest_houses || []).map(h => (
            <button
              key={`s-${h.house}`}
              type="button"
              className="hl-chip hl-chip--strong"
              onClick={() => setFocusHouse(h.house)}
            >
              🟢 H{h.house} {h.theme_en}
            </button>
          ))}
          {(s.weakest_houses || []).map(h => (
            <button
              key={`w-${h.house}`}
              type="button"
              className="hl-chip hl-chip--weak"
              onClick={() => setFocusHouse(h.house)}
            >
              🔴 H{h.house}
            </button>
          ))}
        </div>
      </header>

      <section className="hl-dasa-section" aria-label="D1 reference chart">
        <header className="hl-dasa-section__head">
          <h3 className="hl-dasa-section__title">
            <Bilingual en="D1 Rasi — quick reference" ta="D1 ராசி — விரைவு குறிப்பு" inline />
          </h3>
          <p className="hl-dasa-section__sub">Orange tint = active life areas in current Dasa</p>
        </header>
        <div className="hl-dasa-grid">
          <D1ReferenceChart chart={chart} focusHouses={dasaFocusHouses} />
          <DasaLifeAreas
            dasa={data.dasa_life_areas}
            focusHouse={focusHouse}
            onSelectHouse={setFocusHouse}
          />
        </div>
      </section>

      <div className="hl-layout">
        <section className="hl-graph-wrap">
          <div className="hl-graph-toolbar">
            <label htmlFor="hl-focus-select" className="hl-graph-toolbar__label">Focus house</label>
            <select
              id="hl-focus-select"
              className="hl-focus-select"
              value={focusHouse}
              onChange={e => setFocusHouse(Number(e.target.value))}
            >
              {(data.houses || []).map(h => (
                <option key={h.house} value={h.house}>
                  H{h.house} — {h.theme_en} ({h.lord})
                </option>
              ))}
            </select>
          </div>
          <HouseLinksGraph
            graph={data.graph}
            focusHouse={focusHouse}
            onSelectHouse={setFocusHouse}
          />
          <p className="hl-graph-hint">Tap a house node to focus · lines show lord & pada links</p>
        </section>

        <section className="hl-pred-wrap">
          <PredictionCard pred={focusPred} houseRow={houseMap[focusHouse]} />
        </section>
      </div>

      <details className="hl-section" open={false}>
        <summary className="hl-section__summary">
          <Bilingual en="All 12 houses" ta="12 வீடுகள்" inline />
        </summary>
        <div className="hl-house-grid">
          {(data.houses || []).map(h => (
            <button
              key={h.house}
              type="button"
              className={`hl-house-card hl-house-card--${h.rag?.status || 'moderate'} ${focusHouse === h.house ? 'hl-house-card--focus' : ''}`}
              onClick={() => setFocusHouse(h.house)}
            >
              <span className="hl-house-card__num">H{h.house}</span>
              <span className="hl-house-card__theme">{h.theme_en}</span>
              <span className="hl-house-card__lord">{h.lord} → H{h.lord_house}</span>
              <span className="hl-house-card__score">{h.rag?.emoji} {h.strength}</span>
            </button>
          ))}
        </div>
      </details>

      <details className="hl-section">
        <summary className="hl-section__summary">
          <Bilingual en="Lord-link yogas" ta="அதிபதி யோகங்கள்" inline />
          <span className="hl-section__count">({(data.yogas || []).length})</span>
        </summary>
        <YogaList yogas={data.yogas} />
      </details>
    </div>
  )
}
