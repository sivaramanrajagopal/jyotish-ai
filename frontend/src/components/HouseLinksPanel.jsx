/**
 * HouseLinksPanel — which houses are active now and why.
 * Now: the dasha lords switch houses on; Jupiter and Saturn trigger them.
 * Houses: one row per house with its links, dasha, transit and BPHS line.
 * The connection map stays behind a button.
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'
import { classicalForHouse, useClassicalRules } from '../hooks/useClassicalRules'
import HouseLinksGraph from './HouseLinksGraph'
import SouthIndianChart from './SouthIndianChart'

const TONE_TO_RAG = { good: 'strong', mixed: 'moderate', hard: 'weak' }

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

function Line({ en, ta }) {
  return (
    <li>
      {en}.
      {ta && <span className="hl-line__ta">{ta}</span>}
    </li>
  )
}

function StatusBadge({ status }) {
  if (!status) return null
  return <span className={`hl-badge hl-badge--${status.key}`}>{status.en}</span>
}

function FruitBadge({ fruit }) {
  if (!fruit?.en) return null
  return <span className={`hl-badge hl-badge--fruit-${fruit.tone}`}>{fruit.en.replace(/\.$/, '')}</span>
}

function transitSummary(row) {
  const t = row.transit || {}
  if (t.jupiter && t.saturn) return 'Jupiter and Saturn both touch it now'
  if (t.jupiter) return 'Jupiter touches it now, Saturn does not yet'
  if (t.saturn) return 'Saturn touches it now, Jupiter does not yet'
  return 'Neither Jupiter nor Saturn touches it yet'
}

function NowCard({ activation, rows, onOpen }) {
  if (!activation) return null
  const p = activation.period
  const now = (activation.now || []).map(h => rows[h]).filter(Boolean)
  const sky = (activation.sky_only || []).map(h => rows[h]).filter(Boolean)
  return (
    <section className="hl-now" aria-label="Active now">
      <h3 className="hl-now__title">
        <Bilingual en="Active now" ta="இப்போது செயலில்" inline />
      </h3>
      {p && (
        <p className="hl-now__period">
          <strong>{p.mahadasha.planet}</strong> mahadasha to {p.mahadasha.end}
          {' · '}
          <strong>{p.bhukti.planet}</strong> bhukti to {p.bhukti.end}
          {p.days_left >= 0 ? ` (${p.days_left} days left)` : ''}
          {p.next_bhukti ? ` · ${p.next_bhukti.planet} bhukti from ${p.next_bhukti.start}` : ''}
        </p>
      )}
      {activation.relation && (
        <p className={`hl-now__line hl-now__line--${activation.relation.tone}`}>
          {activation.relation.en}
          <span className="hl-line__ta">{activation.relation.ta}</span>
        </p>
      )}
      {activation.today && (
        <p className="hl-now__line">
          {activation.today.en}
          <span className="hl-line__ta">{activation.today.ta}</span>
        </p>
      )}
      <ul className="hl-now__list">
        {now.map(row => (
          <li key={row.house}>
            <button type="button" className="hl-now__item" onClick={() => onOpen(row.house)}>
              <span className="hl-now__head">
                <strong>{row.ordinal} · {row.theme_en}</strong>
                <StatusBadge status={row.status} />
              </span>
              <span className="hl-now__why">{row.dasha.reasons[0]?.en}.</span>
              <span className="hl-now__why">{transitSummary(row)}.</span>
            </button>
          </li>
        ))}
      </ul>
      {sky.length > 0 && (
        <p className="hl-now__line hl-now__line--muted">
          Jupiter and Saturn also touch{' '}
          {sky.map(r => `the ${r.ordinal} (${r.theme_en.toLowerCase()})`).join(', ')}
          , with no dasha link to it now.
        </p>
      )}
    </section>
  )
}

function windowText(windows) {
  if (!windows?.length) return 'Jupiter and Saturn do not both touch it in this period'
  return `Jupiter and Saturn both touch it ${windows.map(w => `${w.start} to ${w.end}`).join(', and ')}`
}

function NextStrip({ upcoming }) {
  if (!upcoming?.periods?.length) return null
  return (
    <section className="hl-next" aria-label="Coming next">
      <h3 className="hl-section-title">
        <Bilingual en="Coming next" ta="அடுத்து வருவது" inline />
      </h3>
      <ol className="hl-next__list">
        {upcoming.periods.map(p => (
          <li key={`${p.mahadasha}-${p.bhukti}-${p.start}`} className="hl-next__item">
            <p className="hl-next__head">
              <strong>{p.bhukti} bhukti</strong>
              <span className="hl-next__dates">{p.mahadasha} mahadasha · {p.start} to {p.end}</span>
            </p>
            {p.relation && (
              <p className={`hl-now__line hl-now__line--${p.relation.tone}`}>
                {p.relation.en}
                <span className="hl-line__ta">{p.relation.ta}</span>
              </p>
            )}
            <ul className="hl-next__houses">
              {p.houses.map(h => (
                <li key={h.house}>
                  <strong>{h.ordinal} · {h.theme_en}</strong>
                  <span className="hl-bi__ta"> · {h.theme_ta}</span>
                  <span className={`hl-next__window${h.windows.length ? ' hl-next__window--on' : ''}`}>
                    {windowText(h.windows)}.
                  </span>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ol>
      {upcoming.sign_changes?.length > 0 && (
        <details className="hl-section">
          <summary className="hl-section__summary">
            <Bilingual en={`Jupiter and Saturn sign changes to ${upcoming.through}`} ta="குரு, சனி ராசி மாற்றங்கள்" inline />
            <span className="hl-section__count">({upcoming.sign_changes.length})</span>
          </summary>
          <ul className="hl-next__changes">
            {upcoming.sign_changes.map(s => (
              <li key={`${s.planet}-${s.iso}`}>
                {s.en}
                <span className="hl-line__ta">{s.ta}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  )
}

function HouseRow({ row, classical, open, onToggle }) {
  const t = row.transit || {}
  const reasons = row.dasha?.reasons || []
  return (
    <li id={`hl-row-${row.house}`} className={`hl-row${open ? ' hl-row--open' : ''}`}>
      <button type="button" className="hl-row__head" aria-expanded={open} onClick={onToggle}>
        <span className="hl-row__title">
          <strong>{row.ordinal}</strong> · {row.theme_en}
          <span className="hl-bi__ta"> · {row.theme_ta}</span>
        </span>
        <span className="hl-row__tags">
          <StatusBadge status={row.status} />
          <FruitBadge fruit={row.fruit} />
        </span>
        <span className="hl-row__lord">{row.sign} · lord {row.lord} in the {row.lord_house}{ordSuffix(row.lord_house)}</span>
      </button>
      {open && (
        <div className="hl-row__body">
          <h4>How it is tied</h4>
          <ul>{(row.links || []).map(l => <Line key={l.en} en={l.en} ta={l.ta} />)}</ul>

          <h4>Dasha</h4>
          {reasons.length ? (
            <ul>{reasons.map(r => <Line key={r.en} en={`${r.en}${r.level === 'side' ? ' (side)' : ''}`} ta={r.ta} />)}</ul>
          ) : (
            <p className="hl-row__muted">The running lords do not touch this house.</p>
          )}

          <h4>Transit today</h4>
          {(t.lines || []).length ? (
            <ul>{t.lines.map(l => <Line key={l.en} en={l.en} ta={l.ta} />)}</ul>
          ) : (
            <p className="hl-row__muted">Jupiter and Saturn are not touching this house or its lord.</p>
          )}
          <p className="hl-row__muted">
            {t.planets_now?.length ? `In this sign now: ${t.planets_now.join(', ')}. ` : ''}
            {t.sav_label ? `Sarvashtakavarga ${t.sav_label.toLowerCase()}.` : ''}
          </p>

          {classical && (
            <>
              <h4>Classical</h4>
              <p className="hl-row__classical">
                {classical.source.cite}
                {classical.strength_label ? ` · ${classical.strength_label}. ` : ' '}
                {classical.summary}
              </p>
            </>
          )}
          <p className="hl-row__muted">How well it gives: {row.fruit?.en} {row.fruit?.ta}</p>
        </div>
      )}
    </li>
  )
}

function ordSuffix(n) {
  if (n % 100 >= 10 && n % 100 <= 20) return 'th'
  return { 1: 'st', 2: 'nd', 3: 'rd' }[n % 10] || 'th'
}

function YogaList({ yogas }) {
  if (!yogas?.length) {
    return <p className="hl-muted">No kendra–trikona or dharma–karma lord yogas found.</p>
  }
  return (
    <ul className="hl-yoga-list">
      {yogas.map(y => (
        <li key={`${y.name}-${y.lords.join('-')}`} className="hl-yoga-list__item">
          <strong>{y.name}</strong>
          <span className="hl-yoga-list__ta">{y.name_ta}</span>
          <p>{y.detail_en}</p>
        </li>
      ))}
    </ul>
  )
}

function MapSection({ data, chart, rows, focusHouse, setFocusHouse }) {
  const graph = useMemo(() => ({
    ...data.graph,
    nodes: (data.graph?.nodes || []).map(n => ({ ...n, rag: TONE_TO_RAG[rows[n.house]?.fruit?.tone] || 'moderate' })),
  }), [data.graph, rows])
  const pred = (data.predictions || []).find(p => p.house === focusHouse)
  const activeHouses = (data.activation?.rows || []).filter(r => r.dasha?.level).map(r => r.house)
  const bd = chart.birth_data || {}
  return (
    <div className="hl-map">
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
              {h.house}{ordSuffix(h.house)} · {h.theme_en} ({h.lord})
            </option>
          ))}
        </select>
      </div>
      <div className="hl-layout">
        <section className="hl-graph-wrap">
          <HouseLinksGraph graph={graph} focusHouse={focusHouse} onSelectHouse={setFocusHouse} />
          <p className="hl-graph-hint">Lines show this house’s links. Green supports, red dashed strains.</p>
        </section>
        <section className="hl-graph-wrap">
          <SouthIndianChart
            title="D1"
            subtitle={`${bd.dob || ''} · ${bd.tob || ''}`}
            planetPositions={chart.planet_positions}
            lagnaSignIndex={chart.ascendant?.sign_index ?? 0}
            variant="classic"
            showDetails={false}
            chartKind="natal"
            highlightBhavaHouses={activeHouses}
          />
          <p className="hl-graph-hint">Tinted houses are switched on by the running dasha.</p>
        </section>
      </div>
      {pred && (
        <div className="hl-map__detail">
          <p>
            <strong>Feeds in from:</strong> {(pred.channels_in || []).map(h => `${h}${ordSuffix(h)}`).join(', ') || 'none'}
            {' · '}
            <strong>Feeds out to:</strong> {(pred.channels_out || []).map(h => `${h}${ordSuffix(h)}`).join(', ') || 'none'}
          </p>
          {(pred.incoming_edges || []).length > 0 && (
            <ul className="hl-edges">
              {pred.incoming_edges.map(e => (
                <li key={e.id} className={e.supportive === false ? 'hl-edges__stress' : ''}>{e.label_en}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}

export default function HouseLinksPanel({ chart, userId, enabled = true }) {
  const [result, setResult] = useState({ chart: null, data: null, error: '' })
  const [openHouse, setOpenHouse] = useState(null)
  const [showMap, setShowMap] = useState(false)
  const [focusHouse, setFocusHouse] = useState(10)
  const classical = useClassicalRules(chart, userId, enabled)

  useEffect(() => {
    if (!chart || !enabled) return undefined
    let cancel = false
    api.post('/house-connections/analyze', chartPayload(chart, userId))
      .then(r => {
        if (!cancel) setResult({ chart, data: r.data, error: '' })
      })
      .catch(e => {
        if (!cancel) setResult({ chart, data: null, error: e.response?.data?.detail || 'Could not load House Links.' })
      })
    return () => { cancel = true }
  }, [chart, userId, enabled])

  const current = result.chart === chart
  const data = current ? result.data : null
  const error = current ? result.error : ''
  const loading = Boolean(chart && enabled && !current)

  const rows = useMemo(() => {
    const m = {}
    for (const r of data?.activation?.rows || []) m[r.house] = r
    return m
  }, [data])

  const openFromNow = useCallback(house => {
    setOpenHouse(house)
    requestAnimationFrame(() => {
      document.getElementById(`hl-row-${house}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }, [])

  if (!chart) {
    return <div className="hl-panel hl-panel--muted">Open My Chart first…</div>
  }
  if (loading && !data) return <div className="hl-loading">Building house map…</div>
  if (error) return <div className="hl-error" role="alert">{error}</div>
  if (!data) return null

  const activation = data.activation

  return (
    <div className="hl-panel" id="house-links-panel">
      <header className="hl-hero">
        <h2 className="hl-hero__title">
          <Bilingual en="House Links" ta="வீட்டு தொடர்பு" inline />
        </h2>
        <p className="hl-hero__meta">
          The dasha switches houses on. Jupiter and Saturn touching the house or its lord says the time is now.
        </p>
      </header>

      {activation ? (
        <NowCard activation={activation} rows={rows} onOpen={openFromNow} />
      ) : (
        <p className="hl-error" role="alert">The dasha and transit layer could not be built for this chart.</p>
      )}

      <NextStrip upcoming={data.upcoming} />

      {activation && (
        <section aria-label="All 12 houses">
          <h3 className="hl-section-title">
            <Bilingual en="All 12 houses" ta="12 வீடுகள்" inline />
          </h3>
          <ul className="hl-rows">
            {activation.rows.map(row => (
              <HouseRow
                key={row.house}
                row={row}
                classical={classicalForHouse(classical.data, row.house)}
                open={openHouse === row.house}
                onToggle={() => setOpenHouse(openHouse === row.house ? null : row.house)}
              />
            ))}
          </ul>
        </section>
      )}

      <details className="hl-section">
        <summary className="hl-section__summary">
          <Bilingual en="Lord-link yogas" ta="அதிபதி யோகங்கள்" inline />
          <span className="hl-section__count">({(data.yogas || []).length})</span>
        </summary>
        <YogaList yogas={data.yogas} />
      </details>

      <button
        type="button"
        className="hl-map-toggle"
        aria-expanded={showMap}
        onClick={() => setShowMap(v => !v)}
      >
        {showMap ? 'Hide map' : 'Show map'}
      </button>
      {showMap && (
        <MapSection data={data} chart={chart} rows={rows} focusHouse={focusHouse} setFocusHouse={setFocusHouse} />
      )}

      {data.disclaimer?.en && (
        <p className="hl-disclaimer" role="note">
          {data.disclaimer.en}
          <span className="hl-line__ta">{data.disclaimer.ta}</span>
        </p>
      )}
    </div>
  )
}
