/**
 * AvasthaPanel — Sthula/Sukshma planetary state scorecard + Dasa–Bhukti synergy.
 * Plain-language meanings kept short so the tab stays light and intuitive.
 */
import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'

const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']

const CLASS_TIER = {
  'Immediate & High Manifestation': 'av-tier--peak',
  'Conditional / Strategic Manifestation': 'av-tier--good',
  'Delayed / Sluggish Manifestation': 'av-tier--slow',
  'Blocked / Distressed Manifestation': 'av-tier--blocked',
  'Peak Fructification': 'av-tier--peak',
  'Progressive Growth': 'av-tier--good',
  'Inertia / Delays': 'av-tier--slow',
  'High Friction': 'av-tier--blocked',
}

/** Short badge text — full class stays on title attribute */
const CLASS_SHORT = {
  'Immediate & High Manifestation': 'High',
  'Conditional / Strategic Manifestation': 'Strategic',
  'Delayed / Sluggish Manifestation': 'Delayed',
  'Blocked / Distressed Manifestation': 'Blocked',
  'Peak Fructification': 'Peak',
  'Progressive Growth': 'Growth',
  'Inertia / Delays': 'Delays',
  'High Friction': 'Friction',
}

const STHULA_MEANING = {
  Deepta: 'Bright / strongly expressive',
  Sthamitha: 'Stable in own strength',
  Muditha: 'Comfortable / supported',
  Santha: 'Calm / moderate output',
  Sakta: 'Constrained (often by retrograde)',
  Heenasakstha: 'Weakened capacity',
  Deena: 'Distressed / inimical setting',
  Peethya: 'Edge of sign — unstable',
  Peeda: 'Pressured by fast motion',
  Vikala: 'Impaired (combust)',
  Kala: 'Dark / debilitated',
}

const SUKSHMA_MEANING = {
  Sayana: 'Resting — slow to deliver',
  Upaveshana: 'Seated — preparing',
  Netrapani: 'Watching — strategic',
  Prakasha: 'Fully lit — peak output',
  Gamana: 'In transit — unstable',
  Aagamana: 'Arriving — productive',
  Aasthani: 'Settled high — peak output',
  Aagama: 'Coming in — material gains',
  Bhoji: 'Enjoying — high yield',
  Nritya: 'Active dance — productive',
  Kauthuka: 'Curious — moderate',
  Nidra: 'Asleep — dormant',
}

function classifyCombined(net) {
  if (net >= 80) return 'Peak Fructification'
  if (net >= 50) return 'Progressive Growth'
  if (net >= 25) return 'Inertia / Delays'
  return 'High Friction'
}

function synergyOutcomes(klass) {
  const map = {
    'Peak Fructification': [
      'Both period lords are working well together.',
      'Good window for decisive action and visible gains.',
    ],
    'Progressive Growth': [
      'Steady progress with planning and follow-through.',
      'Prefer structured goals over sudden leaps.',
    ],
    'Inertia / Delays': [
      'Results may come late or need more effort.',
      'Favour maintenance over big new launches.',
    ],
    'High Friction': [
      'This lord pair tends to block or frustrate output.',
      'Keep stakes low; use for review and remedies.',
    ],
  }
  return map[klass] || []
}

function StatusBadge({ klass }) {
  const tier = CLASS_TIER[klass] || 'av-tier--good'
  const short = CLASS_SHORT[klass] || klass
  return (
    <span className={`av-badge ${tier}`} title={klass}>
      {short}
    </span>
  )
}

function RemedyBlock({ remedy }) {
  if (!remedy) return null
  return (
    <section className="av-remedy" aria-label="Recommended classical remedies">
      <h5 className="av-remedy__title">Recommended classical remedies</h5>
      <p className="av-remedy__objective">
        {remedy.objective}
        {remedy.objective_ta ? (
          <span className="av-remedy__ta">{remedy.objective_ta}</span>
        ) : null}
      </p>
      <p className="av-remedy__approach">{remedy.approach}</p>
      {remedy.items?.length > 0 && (
        <ul className="av-remedy__list">
          {remedy.items.map((item) => (
            <li key={item.kind}>
              <span className="av-remedy__kind">{item.label}</span>
              <span className="av-remedy__text">
                {item.text}
                {item.detail ? ` — ${item.detail}` : ''}
              </span>
              {item.text_ta ? (
                <span className="av-remedy__ta">{item.text_ta}</span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
      {(remedy.cautions || []).map((line) => (
        <p key={line} className="av-remedy__caution">{line}</p>
      ))}
      {remedy.note ? <p className="av-remedy__note">{remedy.note}</p> : null}
    </section>
  )
}

function MeaningGlossary() {
  return (
    <details className="av-primer">
      <summary className="av-primer__summary">What do the state names mean?</summary>
      <div className="av-primer__body">
        <p className="av-glossary__lead">
          <strong>Sthula</strong> = how strong the planet’s “engine” is.
          {' '}<strong>Sukshma</strong> = how awake that engine is right now in the chart math.
        </p>
        <div className="av-glossary-grid">
          <div>
            <h4 className="av-glossary__h">Sthula (capacity)</h4>
            <ul className="av-glossary">
              {Object.entries(STHULA_MEANING).map(([k, v]) => (
                <li key={k}><strong>{k}</strong> — {v}</li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="av-glossary__h">Sukshma (efficiency)</h4>
            <ul className="av-glossary">
              {Object.entries(SUKSHMA_MEANING).map(([k, v]) => (
                <li key={k}><strong>{k}</strong> — {v}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </details>
  )
}

export default function AvasthaPanel({ chart, userId, enabled = true }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dasaLord, setDasaLord] = useState('')
  const [bhuktiLord, setBhuktiLord] = useState('')
  const [breakdownPlanet, setBreakdownPlanet] = useState(null)
  const drawerRef = useRef(null)

  useEffect(() => {
    if (breakdownPlanet) drawerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [breakdownPlanet])

  const load = useCallback(() => {
    if (!chart || !enabled) return
    setLoading(true)
    setError('')
    api.post('/avastha/analyze', chartPayload(chart, userId))
      .then((r) => {
        setData(r.data)
        const s = r.data?.summary || {}
        setDasaLord(s.current_dasa || 'Jupiter')
        setBhuktiLord(s.current_bhukti || 'Venus')
      })
      .catch((e) => {
        const detail = e.response?.data?.detail
        setError(typeof detail === 'string' ? detail : 'Could not load Avastha analysis.')
      })
      .finally(() => setLoading(false))
  }, [chart, userId, enabled])

  useEffect(() => { load() }, [load])

  const byName = useMemo(() => {
    const map = {}
    for (const p of data?.planets || []) map[p.planet] = p
    return map
  }, [data])

  const synergy = useMemo(() => {
    const d = byName[dasaLord]
    const b = byName[bhuktiLord]
    if (!d || !b) return data?.dasa_bhukti || null
    const combined = Math.round(((d.manifestation.net + b.manifestation.net) / 2) * 100) / 100
    const klass = classifyCombined(combined)
    return {
      dasaLord,
      bhuktiLord,
      dasaClass: d.manifestation.class,
      bhuktiClass: b.manifestation.class,
      manifestationClass: klass,
      objectiveOutcome: synergyOutcomes(klass),
    }
  }, [byName, dasaLord, bhuktiLord, data])

  const breakdownRow = breakdownPlanet ? byName[breakdownPlanet] : null

  if (!enabled) {
    return <div className="td-loading" style={{ opacity: 0.6 }}>Open Avastha tab after calculating your chart…</div>
  }
  if (loading && !data) return <div className="td-loading">Computing planetary avasthas…</div>
  if (error) return <div className="td-error" role="alert">{error}</div>
  if (!data) return null

  const s = data.summary || {}
  const meta = data.metadata || {}

  return (
    <div className="td-panel av-panel">
      <div className="av-disclaimer" role="note">
        <strong>Analytical aid</strong>
        <span> describing classical planetary states. For medical, legal or financial matters, consult a qualified professional.</span>
      </div>

      <div className="av-hero">
        <div className="av-hero__top">
          <span className="av-hero__label">What is Avastha?</span>
        </div>
        <p className="av-hero__headline">
          Avastha is a planet’s <em>condition</em>: its capacity (Sthula) and how awake it is
          (Sukshma), read together into one band per planet.
        </p>
        <p className="av-hero__meta">
          Strongest: <strong>{s.peak_planet}</strong> · Weakest:{' '}
          <strong>{s.lowest_planet}</strong> · Current period:{' '}
          <strong>{s.current_dasa}–{s.current_bhukti}</strong>
        </p>
      </div>

      <details className="av-primer" open>
        <summary className="av-primer__summary">How to read this tab (30 seconds)</summary>
        <div className="av-primer__body">
          <ol className="av-howto">
            <li><strong>Capacity</strong> — strength from dignity. Combustion, debilitation and the last degree weigh heavily; fast motion and retrogression weigh lightly.</li>
            <li><strong>Efficiency</strong> — the Sukshma state, how awake the planet is.</li>
            <li><strong>Band</strong> — capacity and efficiency read together; both need to be decent.</li>
            <li><strong>Dasa × Bhukti</strong> — the two period lords’ birth-chart condition, read together.</li>
          </ol>
          <p className="av-howto__bands">
            Bands, strongest first: <span className="av-tier--peak av-inline">High</span>
            {' · '}
            <span className="av-tier--good av-inline">Strategic</span>
            {' · '}
            <span className="av-tier--slow av-inline">Delayed</span>
            {' · '}
            <span className="av-tier--blocked av-inline">Blocked</span>
          </p>
        </div>
      </details>

      <MeaningGlossary />

      <h3 className="av-section-title">Planetary scorecard</h3>
      <div className="av-table-wrap">
        <table className="av-table">
          <thead>
            <tr>
              <th>Planet</th>
              <th>Capacity</th>
              <th>Efficiency</th>
              <th>Band</th>
            </tr>
          </thead>
          <tbody>
            {(data.planets || []).map((p) => (
              <tr key={p.planet}>
                <td>
                  <button
                    type="button"
                    className="av-planet-btn"
                    onClick={() => setBreakdownPlanet(p.planet)}
                    title="Show calculation steps"
                  >
                    <strong>{p.planet}</strong>
                    <span className="av-planet-btn__sub">
                      {p.sign} {p.degree_in_rasi?.toFixed?.(1)}°
                      {p.is_retrograde ? ' ℞' : ''}
                      {p.is_combust ? ' combust' : ''}
                      {p.is_accelerated ? ' fast' : ''}
                    </span>
                  </button>
                </td>
                <td>
                  <div className="av-state-cell" title={STHULA_MEANING[p.sthula.name] || ''}>
                    <span>{p.sthula.name}</span>
                  </div>
                  <span className="av-state-cell__hint">
                    {STHULA_MEANING[p.sthula.name] || p.sign_dignity}
                  </span>
                </td>
                <td>
                  <div className="av-state-cell" title={SUKSHMA_MEANING[p.sukshma.name] || ''}>
                    <span>{p.sukshma.name}</span>
                  </div>
                  <span className="av-state-cell__hint">
                    {SUKSHMA_MEANING[p.sukshma.name]}
                  </span>
                </td>
                <td>
                  <StatusBadge klass={p.manifestation.class} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="av-hint">Tap a planet for the Sukshma math steps (optional audit).</p>

      <h3 className="av-section-title">Dasa–Bhukti synergy</h3>
      <p className="av-synergy__intro">
        The two lords’ <strong>birth-chart condition</strong>, read together.
        Starts on the current Mahadasha and Bhukti; change the dropdowns to explore other pairs.
      </p>
      <div className="av-synergy">
        <div className="av-synergy__controls">
          <label className="av-select">
            <span>Dasa lord</span>
            <select value={dasaLord} onChange={(e) => setDasaLord(e.target.value)}>
              {PLANETS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </label>
          <label className="av-select">
            <span>Bhukti lord</span>
            <select value={bhuktiLord} onChange={(e) => setBhuktiLord(e.target.value)}>
              {PLANETS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </label>
        </div>
        {synergy && (
          <div className="av-synergy__result">
            <div className="av-synergy__detail">
              <p className="av-synergy__math">
                <strong>{synergy.dasaLord} × {synergy.bhuktiLord}</strong>{' '}
                <StatusBadge klass={synergy.manifestationClass} />
              </p>
              {synergy.dasaClass && (
                <p className="av-synergy__math">
                  {synergy.dasaLord} <StatusBadge klass={synergy.dasaClass} />
                  {' · '}
                  {synergy.bhuktiLord} <StatusBadge klass={synergy.bhuktiClass} />
                </p>
              )}
              <ul className="av-synergy__outcomes">
                {(synergy.objectiveOutcome || []).map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      <details className="av-primer av-tech">
        <summary className="av-primer__summary">Technical inputs (for verification)</summary>
        <div className="av-primer__body">
          <p>
            Lagna rasi #{meta.lagnaRasiIndex} · Janma nak #{meta.janmaNakshatraIndex} ·
            Nazhikai after sunrise <strong>{meta.birthNazhikaiAfterSunrise}</strong>
            {meta.sunrise_local && (
              <> (sunrise {meta.sunrise_local.slice(0, 16).replace('T', ' ')})</>
            )}
          </p>
          <p>
            The band is the geometric mean of capacity and efficiency. Light penalties: Athi Vega
            (fast direct motion) and retrogression, which the nodes skip. Heavy: combust,
            debilitated, last degree.
          </p>
        </div>
      </details>

      {breakdownRow && (
        <div ref={drawerRef} className="av-drawer" role="dialog" aria-label="Sukshma calculation breakdown">
          <div className="av-drawer__head">
            <h4>
              {breakdownRow.planet}: {breakdownRow.sukshma.name}
              <span className="av-drawer__meaning">
                {' '}— {SUKSHMA_MEANING[breakdownRow.sukshma.name]}
              </span>
            </h4>
            <button type="button" className="av-drawer__close" onClick={() => setBreakdownPlanet(null)}>
              Close
            </button>
          </div>
          <p className="av-drawer__sthula">
            Capacity: <strong>{breakdownRow.sthula.name}</strong>
            {' '}— {STHULA_MEANING[breakdownRow.sthula.name] || breakdownRow.sthula.reason}
          </p>
          <ol className="av-drawer__steps">
            <li>
              Planet × Nakshatra = <code>{breakdownRow.sukshma.breakdown.step1}</code>
              {' '}({breakdownRow.planet_index} × {breakdownRow.nakshatra_index})
            </li>
            <li>
              floor(× degree) = <code>{breakdownRow.sukshma.breakdown.step2}</code>
              {' '}({breakdownRow.degree_in_rasi}°)
            </li>
            <li>
              + janma + lagna + nazhikai = <code>{breakdownRow.sukshma.breakdown.step3}</code>
            </li>
            <li>
              mod 12 → index <code>{breakdownRow.sukshma.breakdown.avastha_index}</code>
              {' '}→ <strong>{breakdownRow.sukshma.name}</strong>
            </li>
          </ol>
          <p className="av-drawer__formula">{breakdownRow.sukshma.breakdown.formula}</p>
          <RemedyBlock remedy={breakdownRow.remedy} />
        </div>
      )}
    </div>
  )
}
