/**
 * CareerPanel — D1 + D10 charts, 10 rules, profession tags, Dasa timing.
 */
import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'
import SouthIndianChart from './SouthIndianChart'

function StrengthBadge({ strength }) {
  const cls = {
    Strong: 'cr-strength--strong',
    Good: 'cr-strength--good',
    Moderate: 'cr-strength--moderate',
    Developing: 'cr-strength--dev',
  }[strength] || 'cr-strength--moderate'
  return <span className={`cr-strength ${cls}`}>{strength || '—'}</span>
}

function ProfessionTags({ tags }) {
  if (!tags?.length) return null
  return (
    <div className="cr-tags" role="list">
      {tags.map(t => (
        <div key={t.name} className="cr-tag" role="listitem">
          <span className="cr-tag__name">{t.name}</span>
          <span className="cr-tag__pct">{t.probability}%</span>
          {t.reasons?.[0] && <span className="cr-tag__hint">{t.reasons[0]}</span>}
        </div>
      ))}
    </div>
  )
}

function RulesChecklist({ rules }) {
  const [open, setOpen] = useState(true)
  if (!rules?.length) return null
  const matched = rules.filter(r => r.matched).length
  return (
    <section className="td-card cr-rules">
      <button type="button" className="td-section__toggle" onClick={() => setOpen(o => !o)}>
        <span>10 career rules ({matched}/10 matched)</span>
        <span aria-hidden="true">{open ? '▾' : '▸'}</span>
      </button>
      {open && (
        <ul className="cr-rules__list">
          {rules.map(r => (
            <li key={r.id} className={r.matched ? 'cr-rules__item--yes' : 'cr-rules__item--no'}>
              <span className="cr-rules__mark">{r.matched ? '✓' : '○'}</span>
              <div>
                <strong>R{r.id}</strong> {r.label}
                <p className="cr-rules__detail">{r.detail}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function TimingTable({ title, rows, emptyText }) {
  if (!rows?.length) {
    return (
      <article className="td-card">
        <h4 className="td-card__title">{title}</h4>
        <p className="td-card__hint">{emptyText}</p>
      </article>
    )
  }
  return (
    <article className="td-card">
      <h4 className="td-card__title">{title}</h4>
      <div className="cr-table-wrap">
        <table className="cr-table">
          <thead>
            <tr>
              <th>Period</th>
              <th>Start</th>
              <th>End</th>
              <th>Links</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={`${row.start}-${i}`}>
                <td>{row.label}</td>
                <td>{row.start}</td>
                <td>{row.end}</td>
                <td>{(row.links || []).join(', ') || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  )
}

function FullTiming({ periods }) {
  const [open, setOpen] = useState(false)
  if (!periods?.length) return null
  return (
    <section className="td-section td-section--tier3">
      <button type="button" className="td-section__toggle" onClick={() => setOpen(o => !o)}>
        <span>Full career Dasa timeline ({periods.length} windows)</span>
        <span aria-hidden="true">{open ? '▾' : '▸'}</span>
      </button>
      {open && (
        <div className="cr-table-wrap">
          <table className="cr-table">
            <thead>
              <tr>
                <th>Maha</th>
                <th>Bhukti</th>
                <th>Start</th>
                <th>End</th>
                <th>Links</th>
              </tr>
            </thead>
            <tbody>
              {periods.map((p, i) => (
                <tr key={`${p.start}-${i}`}>
                  <td>{p.maha_dasa}</td>
                  <td>{p.bukti}</td>
                  <td>{p.start}</td>
                  <td>{p.end}</td>
                  <td>{(p.links || []).join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default function CareerPanel({ chart, userId, enabled = true }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    if (!chart || !enabled) return
    setLoading(true)
    setError('')
    api.post('/career/predict', chartPayload(chart, userId))
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Could not load career prediction.'))
      .finally(() => setLoading(false))
  }, [chart, userId, enabled])

  useEffect(() => { load() }, [load])

  if (!enabled) {
    return <div className="td-loading" style={{ opacity: 0.6 }}>Open Career tab after calculating your chart…</div>
  }
  if (loading && !data) return <div className="td-loading">Analyzing D1 + D10 career chart…</div>
  if (error) return <div className="td-error" role="alert">{error}</div>
  if (!data) return null

  const s = data.summary || {}
  const d10Asc = data.dasamsa_ascendant || {}
  const d10Pos = data.dasamsa_positions || {}

  return (
    <div className="td-panel cr-panel">
      <div className="cr-hero">
        <div className="cr-hero__top">
          <span className="cr-hero__label">Career strength</span>
          <StrengthBadge strength={s.career_strength} />
          <span className="cr-hero__rules">{s.rules_matched}/{s.rules_total} rules</span>
        </div>
        {data.hero?.headline && <p className="cr-hero__headline">{data.hero.headline}</p>}
        <p className="cr-hero__meta">
          10th lord <strong>{s.tenth_lord}</strong> ({s.tenth_house_sign}) · AK <strong>{s.atmakaraka}</strong> · AmK <strong>{s.amatyakaraka}</strong>
        </p>
      </div>

      <h3 className="cr-layer-title">Profession suggestions</h3>
      <ProfessionTags tags={data.profession_tags} />

      <h3 className="cr-layer-title">D1 &amp; D10 charts</h3>
      <div className="cr-charts-grid">
        <div className="cr-chart-card">
          <h4 className="cr-chart-card__title">D1 — Rasi Chart (Career houses)</h4>
          <SouthIndianChart
            title="D1"
            subtitle={`${chart.birth_data?.dob || ''} · 10th lord: ${s.tenth_lord}`}
            planetPositions={chart.planet_positions}
            lagnaSignIndex={chart.ascendant?.sign_index}
            variant="classic"
            showDetails
            chartKind="natal"
          />
        </div>
        <div className="cr-chart-card">
          <h4 className="cr-chart-card__title">D10 — Dasamsa Chart</h4>
          <SouthIndianChart
            title="D10"
            subtitle={`Lagna: ${d10Asc.sign || '—'} · lord ${d10Asc.sign_lord || '—'}`}
            planetPositions={d10Pos}
            lagnaSignIndex={d10Asc.sign_index}
            dasamsa
            variant="classic"
            showDetails
            chartKind="natal"
          />
        </div>
      </div>

      <RulesChecklist rules={data.rules} />

      <h3 className="cr-layer-title">Career timing (Dasa / Bhukti)</h3>
      <p className="td-card__hint cr-timing-note">
        Highlights periods when Mahadasha or Bhukti touches 10th lord, Atmakaraka (AK), or Amatyakaraka (AmK).
      </p>
      <div className="cr-grid">
        <TimingTable
          title="Active now"
          rows={data.timing?.current}
          emptyText="No career-linked Dasa/Bhukti active today."
        />
        <TimingTable
          title="Upcoming windows"
          rows={data.timing?.upcoming}
          emptyText="No upcoming career windows in horizon."
        />
      </div>
      <FullTiming periods={data.timing?.all} />

      <p className="td-card__hint cr-disclaimer">{data.interpretation?.note}</p>
    </div>
  )
}
