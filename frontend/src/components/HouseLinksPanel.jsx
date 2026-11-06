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
  if (t.jupiter && t.saturn) {
    return t.double_until
      ? `Jupiter and Saturn both touch it now, until ${t.double_until}`
      : 'Jupiter and Saturn both touch it now'
  }
  if (t.jupiter) return 'Jupiter touches it now; Saturn does not'
  if (t.saturn) return 'Saturn touches it now; Jupiter does not'
  return 'Neither Jupiter nor Saturn touches it now'
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

function HouseTile({ row, view, marks, selected, onSelect }) {
  const t = row.transit || {}
  const level = row.dasha?.level
  return (
    <li>
      <button
        type="button"
        className={`hl-tile hl-tile--${view === 'now' ? row.status.key : row.fruit?.tone}${selected ? ' hl-tile--selected' : ''}`}
        aria-pressed={selected}
        onClick={onSelect}
      >
        <span className="hl-tile__num">{row.ordinal}</span>
        <span className="hl-tile__theme">{row.theme_en}</span>
        <span className="hl-tile__ta">{row.theme_ta}</span>
        {view === 'natal' ? (
          <>
            <span className="hl-tile__lord">{row.lord} in the {row.lord_house}{ordSuffix(row.lord_house)}</span>
            <span className="hl-tile__tags">
              <FruitBadge fruit={row.fruit} />
              {marks.yoga && <span className="hl-badge">Yoga</span>}
              {marks.exchange && <span className="hl-badge">Exchange</span>}
            </span>
          </>
        ) : (
          <>
            <span className="hl-tile__tags">
              <StatusBadge status={row.status} />
            </span>
            <span className="hl-tile__tags">
              {level && <span className="hl-badge">Dasha {level}</span>}
              {t.jupiter && <span className="hl-badge">Jupiter</span>}
              {t.saturn && <span className="hl-badge">Saturn</span>}
            </span>
          </>
        )}
      </button>
    </li>
  )
}

function HouseDetail({ row, view, classical }) {
  if (!row) return null
  const t = row.transit || {}
  const reasons = row.dasha?.reasons || []
  return (
    <article id="hl-detail" className="hl-detail" aria-live="polite">
      <h4 className="hl-detail__title">
        {row.ordinal} · {row.theme_en}
        <span className="hl-bi__ta"> · {row.theme_ta}</span>
      </h4>
      <p className="hl-detail__lede">
        {row.sign} · lord {row.lord} in the {row.lord_house}{ordSuffix(row.lord_house)} · {row.fruit?.en}
        <span className="hl-line__ta">{row.fruit?.ta}</span>
      </p>
      {view === 'natal' ? (
        <>
          <h5>How it is tied</h5>
          <ul>{(row.links || []).map(l => <Line key={l.en} en={l.en} ta={l.ta} />)}</ul>
          {classical && (
            <>
              <h5>Classical</h5>
              <p className="hl-detail__text">
                {classical.source.cite}
                {classical.strength_label ? ` · ${classical.strength_label}. ` : ' '}
                {classical.summary}
              </p>
            </>
          )}
        </>
      ) : (
        <>
          <p className="hl-detail__text"><StatusBadge status={row.status} /></p>
          <h5>Dasha</h5>
          {reasons.length ? (
            <ul>{reasons.map(r => <Line key={r.en} en={`${r.en}${r.level === 'side' ? ' (side)' : ''}`} ta={r.ta} />)}</ul>
          ) : (
            <p className="hl-detail__muted">The running lords do not touch this house.</p>
          )}
          <h5>Transit today</h5>
          {(t.lines || []).length ? (
            <ul>{t.lines.map(l => <Line key={l.en} en={l.en} ta={l.ta} />)}</ul>
          ) : (
            <p className="hl-detail__muted">Jupiter and Saturn are not touching this house or its lord.</p>
          )}
          <p className="hl-detail__muted">
            {t.planets_now?.length ? `In this sign now: ${t.planets_now.join(', ')}. ` : ''}
            {t.sav_label ? `Sarvashtakavarga ${t.sav_label.toLowerCase()}.` : ''}
          </p>
        </>
      )}
    </article>
  )
}

function HouseGrid({ rows, view, marks, selected, onSelect, classical }) {
  const list = Object.values(rows)
  return (
    <section aria-label="All 12 houses">
      <h3 className="hl-section-title">
        <Bilingual en="All 12 houses" ta="12 வீடுகள்" inline />
      </h3>
      <ul className="hl-tiles">
        {list.map(row => (
          <HouseTile
            key={row.house}
            row={row}
            view={view}
            marks={marks[row.house] || {}}
            selected={selected === row.house}
            onSelect={() => onSelect(row.house)}
          />
        ))}
      </ul>
      <HouseDetail row={rows[selected]} view={view} classical={classicalForHouse(classical, selected)} />
    </section>
  )
}

const CODES = [
  ['L', 'its lord sits there', 'அதிபதி அங்கு'],
  ['H', 'that lord sits here', 'அந்த அதிபதி இங்கு'],
  ['X', 'lords exchange signs', 'பரிவர்த்தனை'],
  ['C', 'lords sit together', 'அதிபதிகள் இணைவு'],
  ['M', 'lords aspect each other', 'பரஸ்பர பார்வை'],
  ['A', 'one lord aspects the other, one way', 'ஒரு பக்க பார்வை'],
  ['S', 'one planet rules both', 'ஒரே அதிபதி'],
]

function houseList(houses) {
  return houses?.length ? houses.join(', ') : '–'
}

function NatalTable({ rows }) {
  if (!rows?.length) return null
  return (
    <details className="hl-section" open>
      <summary className="hl-section__summary">
        <Bilingual en="House connections table" ta="வீட்டு தொடர்பு அட்டவணை" inline />
      </summary>
      <div className="hl-tbl-wrap">
        <ul className="hl-tbl-legend">
          {CODES.map(([code, en, ta]) => (
            <li key={code}><strong>{code}</strong> {en} <span className="hl-bi__ta">· {ta}</span></li>
          ))}
        </ul>
        <table className="hl-tbl">
          <colgroup><col style={{ width: '30%' }} /><col style={{ width: '20%' }} /><col /></colgroup>
          <thead>
            <tr><th scope="col">House</th><th scope="col">Lord in</th><th scope="col">Connected houses</th></tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.house}>
                <th scope="row">{r.house}<span className="hl-tbl__sub">{r.theme_en}</span></th>
                <td>{r.lord_house}<span className="hl-tbl__sub">{r.lord}</span></td>
                <td>
                  <span className="hl-tbl__chips">
                    {r.connected.map(c => (
                      <span key={c.house} className="hl-tbl__chip">{c.house}<sup>{c.codes}</sup></span>
                    ))}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}

const BOTH_SHOWN = 3

function DashaTable({ rows }) {
  if (!rows?.length) return null
  return (
    <details className="hl-section" open>
      <summary className="hl-section__summary">
        <Bilingual en="Dasha table" ta="தசை அட்டவணை" inline />
      </summary>
      <div className="hl-tbl-wrap">
        <p className="hl-tbl-note">
          Activated: houses the lord rules or sits in. Connected: houses it aspects or reaches through its star lord.
          Both: dates when Jupiter and Saturn each touch the house or its lord. Bold is an activated house.
        </p>
        <table className="hl-tbl">
          <colgroup><col style={{ width: '31%' }} /><col style={{ width: '19%' }} /><col style={{ width: '19%' }} /><col /></colgroup>
          <thead>
            <tr><th scope="col">Lord</th><th scope="col">Activated</th><th scope="col">Connected</th><th scope="col">Both</th></tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={`${r.planet}-${r.label}-${r.when}`} className={r.current ? 'hl-tbl__row--now' : ''}>
                <th scope="row">
                  {r.planet}
                  <span className="hl-tbl__sub">{r.label}</span>
                  <span className="hl-tbl__sub">{r.when}</span>
                </th>
                <td>{houseList(r.activated)}</td>
                <td>{houseList(r.connected)}</td>
                <td>
                  {r.both.length ? (
                    <>
                      {r.both.slice(0, BOTH_SHOWN).map(b => (
                        <span key={`${b.house}-${b.start}`} className="hl-tbl__both">
                          {b.level === 'main' ? <strong>{b.house}</strong> : b.house}
                          {b.now ? ` now to ${b.end}` : ` ${b.start} to ${b.end}`}
                        </span>
                      ))}
                      {r.both.length > BOTH_SHOWN && (
                        <span className="hl-tbl__sub">and {r.both.length - BOTH_SHOWN} later</span>
                      )}
                    </>
                  ) : '–'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}

function TransitTable({ rows }) {
  if (!rows?.length) return null
  return (
    <details className="hl-section" open>
      <summary className="hl-section__summary">
        <Bilingual en="Transit table, today" ta="கோசார அட்டவணை, இன்று" inline />
      </summary>
      <div className="hl-tbl-wrap">
        <p className="hl-tbl-note">Houses counted from the lagna. Lords of: houses whose lord the planet sits on or aspects.</p>
        <table className="hl-tbl">
          <colgroup><col style={{ width: '27%' }} /><col style={{ width: '20%' }} /><col style={{ width: '22%' }} /><col /></colgroup>
          <thead>
            <tr><th scope="col">Planet</th><th scope="col">In</th><th scope="col">Aspects</th><th scope="col">Lords of</th></tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.planet} className={['Jupiter', 'Saturn'].includes(r.planet) ? 'hl-tbl__row--now' : ''}>
                <th scope="row">
                  {r.planet}{r.retrograde ? ' (R)' : ''}
                  {r.next && <span className="hl-tbl__sub">to {r.next.sign} ({r.next.house}) {r.next.date}</span>}
                </th>
                <td>{r.house}<span className="hl-tbl__sub">{r.sign}</span></td>
                <td>{houseList(r.aspects)}</td>
                <td>{houseList(r.lords_of)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}

function ExchangeList({ edges }) {
  const swaps = (edges || []).filter(e => e.kind === 'exchange')
  if (!swaps.length) return <p className="hl-muted">No sign exchanges between house lords.</p>
  return (
    <ul className="hl-yoga-list">
      {swaps.map(e => {
        const [a, b] = e.planets
        return (
          <li key={e.id} className="hl-yoga-list__item">
            <strong>{e.label_en.split(':')[0]}</strong>
            <p>
              {a}, lord of the {e.from_house}{ordSuffix(e.from_house)}, sits in the {e.to_house}{ordSuffix(e.to_house)}.
              {' '}{b}, lord of the {e.to_house}{ordSuffix(e.to_house)}, sits in the {e.from_house}{ordSuffix(e.from_house)}.
            </p>
          </li>
        )
      })}
    </ul>
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
            highlightBhavaHouses={[focusHouse]}
          />
          <p className="hl-graph-hint">The tinted box is the house selected above.</p>
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
  const [view, setView] = useState('now')
  const [selected, setSelected] = useState(null)
  const [showMap, setShowMap] = useState(false)
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

  const marks = useMemo(() => {
    const m = {}
    for (const y of data?.yogas || []) {
      for (const h of y.houses || []) m[h] = { ...m[h], yoga: true }
    }
    for (const e of data?.edges || []) {
      if (e.kind !== 'exchange') continue
      for (const h of [e.from_house, e.to_house]) m[h] = { ...m[h], exchange: true }
    }
    return m
  }, [data])

  const firstNow = data?.activation?.now?.[0] ?? 1
  const selectedHouse = selected ?? (view === 'now' ? firstNow : 1)

  const showHouse = useCallback(house => {
    setSelected(house)
    requestAnimationFrame(() => {
      document.getElementById('hl-detail')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
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
        <div className="hl-switch" role="group" aria-label="House Links view">
          {[
            ['natal', 'Birth chart', 'ஜாதக அமைப்பு'],
            ['now', 'Dasha and transit', 'தசை & கோசாரம்'],
          ].map(([key, en, ta]) => (
            <button
              key={key}
              type="button"
              className={`hl-switch__btn${view === key ? ' hl-switch__btn--on' : ''}`}
              aria-pressed={view === key}
              onClick={() => { setView(key); setSelected(null) }}
            >
              {en}
              <span className="hl-switch__ta">{ta}</span>
            </button>
          ))}
        </div>
        <p className="hl-hero__meta">
          {view === 'natal'
            ? 'Fixed at birth: where each lord sits, how the lords are tied, and how well each house gives.'
            : 'The dasha switches houses on. Jupiter and Saturn touching the house or its lord says the time is now.'}
        </p>
      </header>

      {!activation && (
        <p className="hl-error" role="alert">The house layer could not be built for this chart.</p>
      )}

      {view === 'now' && activation && (
        <NowCard activation={activation} rows={rows} onOpen={showHouse} />
      )}

      {activation && (
        <HouseGrid
          rows={rows}
          view={view}
          marks={marks}
          selected={selectedHouse}
          onSelect={showHouse}
          classical={classical.data}
        />
      )}

      {view === 'now' && (
        <>
          <DashaTable rows={data.tables?.dasha} />
          <TransitTable rows={data.tables?.transit} />
          <NextStrip upcoming={data.upcoming} />
        </>
      )}

      {view === 'natal' && (
        <>
          <NatalTable rows={data.tables?.natal} />
          <details className="hl-section" open>
            <summary className="hl-section__summary">
              <Bilingual en="Lord-link yogas" ta="அதிபதி யோகங்கள்" inline />
              <span className="hl-section__count">({(data.yogas || []).length})</span>
            </summary>
            <YogaList yogas={data.yogas} />
          </details>
          <details className="hl-section">
            <summary className="hl-section__summary">
              <Bilingual en="Sign exchanges" ta="பரிவர்த்தனை" inline />
              <span className="hl-section__count">({(data.edges || []).filter(e => e.kind === 'exchange').length})</span>
            </summary>
            <ExchangeList edges={data.edges} />
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
            <MapSection data={data} chart={chart} rows={rows} focusHouse={selectedHouse} setFocusHouse={showHouse} />
          )}
        </>
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
