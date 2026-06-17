/**
 * InduLagnaPanel — three-layer wealth lagna: natal promise, tiered activation, meaning.
 */
import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'

const VERDICT_CLASS = {
  supportive: 'il-verdict--supportive',
  mixed: 'il-verdict--mixed',
  challenging: 'il-verdict--challenging',
}

const TONE_CLASS = {
  benefic: 'il-tone--benefic',
  mixed: 'il-tone--mixed',
  challenging: 'il-tone--challenging',
}

function VerdictBadge({ verdict, label }) {
  if (!verdict) return null
  return (
    <span className={`il-verdict ${VERDICT_CLASS[verdict] || 'il-verdict--mixed'}`}>
      {label || verdict}
    </span>
  )
}

function HeroStrip({ hero, summary }) {
  if (!hero && !summary) return null
  return (
    <div className="il-hero">
      <div className="il-hero__top">
        <span className="il-hero__label">Natal promise</span>
        <VerdictBadge verdict={summary?.natal_verdict} label={summary?.natal_verdict_label} />
      </div>
      {hero?.headline && <p className="il-hero__headline">{hero.headline}</p>}
      <div className="il-hero__grid">
        {(hero?.active_primary || []).map(p => (
          <div key={`ap-${p.start}`} className="il-hero__chip il-hero__chip--primary">
            <span className="il-hero__chip-tier">Primary · active</span>
            <span>{p.label}</span>
            <span className="il-hero__chip-dates">{p.start} → {p.end}</span>
          </div>
        ))}
        {(hero?.active_secondary || []).map(p => (
          <div key={`as-${p.start}-${p.planet}`} className="il-hero__chip il-hero__chip--secondary">
            <span className="il-hero__chip-tier">Slow transit · active</span>
            <span>{p.label}</span>
            <span className="il-hero__chip-dates">{p.start} → {p.end}</span>
          </div>
        ))}
        {!hero?.active_primary?.length && !hero?.active_secondary?.length && hero?.next_primary?.[0] && (
          <div className="il-hero__chip il-hero__chip--next">
            <span className="il-hero__chip-tier">Next primary</span>
            <span>{hero.next_primary[0].label}</span>
            <span className="il-hero__chip-dates">from {hero.next_primary[0].start}</span>
          </div>
        )}
      </div>
    </div>
  )
}

function NatalJudgmentCard({ judgment, induLagna }) {
  if (!judgment) return null
  const lord = judgment.lord || {}
  return (
    <article className="td-card td-card--tier1 il-judgment">
      <header className="td-card__head">
        <h4 className="td-card__title">How wealth is judged (natal)</h4>
        <VerdictBadge verdict={judgment.verdict} label={judgment.verdict_label} />
      </header>
      <p className="td-card__line">
        <strong>Indu Lagna:</strong> {induLagna?.english} ({induLagna?.name}) · H{induLagna?.house_from_lagna}
        {' '}— {judgment.house_theme}
      </p>
      <p className="td-card__line">
        <strong>Lagna lord:</strong> {judgment.lagna_lord || '—'}
        {judgment.lagna_lord && judgment.lagna_lord !== lord.planet && (
          <span className="td-card__hint"> (distinct from Indu lord {lord.planet})</span>
        )}
      </p>
      <p className="td-card__line">
        <strong>Indu lord:</strong> {lord.planet} in {lord.sign} (H{lord.house}) ·{' '}
        <span className="il-dignity">{lord.dignity}</span>
        {lord.retrograde ? ' · retrograde' : ''}
      </p>

      <div className="il-subsection">
        <h5 className="il-subsection__title">1. Planets in Indu Lagna</h5>
        {judgment.occupants?.length ? (
          <ul className="il-list">
            {judgment.occupants.map(o => (
              <li key={o.planet} className={`il-list__item ${TONE_CLASS[o.tone] || ''}`}>
                <strong>{o.planet}</strong> — {o.note}
              </li>
            ))}
          </ul>
        ) : (
          <p className="td-card__hint">No planets occupy Indu Lagna.</p>
        )}
      </div>

      <div className="il-subsection">
        <h5 className="il-subsection__title">2. Lord strength</h5>
        <p className="td-card__line">
          {lord.planet} is <strong>{lord.dignity}</strong> in {lord.sign || '—'}
          {lord.deep ? ' (deep exaltation/debilitation)' : ''}.
        </p>
      </div>

      <div className="il-subsection">
        <h5 className="il-subsection__title">3. Aspects on Indu Lagna</h5>
        {judgment.aspects?.length ? (
          <ul className="il-list">
            {judgment.aspects.map(a => (
              <li key={a.planet} className={`il-list__item ${TONE_CLASS[a.tone] || ''}`}>
                {a.note}
              </li>
            ))}
          </ul>
        ) : (
          <p className="td-card__hint">No major classical aspects on Indu Lagna from natal grahas.</p>
        )}
      </div>

      <p className="td-card__how">{judgment.summary}</p>
    </article>
  )
}

function PeriodTable({ title, subtitle, rows, tier, emptyText }) {
  if (!rows?.length) {
    return (
      <article className="td-card">
        <h4 className="td-card__title">{title}</h4>
        {subtitle && <p className="td-card__subtitle">{subtitle}</p>}
        <p className="td-card__hint">{emptyText}</p>
      </article>
    )
  }
  return (
    <article className="td-card">
      <h4 className="td-card__title">{title}</h4>
      {subtitle && <p className="td-card__subtitle">{subtitle}</p>}
      <div className="il-table-wrap">
        <table className="il-table">
          <thead>
            <tr>
              <th>Period</th>
              <th>Start</th>
              <th>End</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={`${tier}-${row.start}-${i}`}>
                <td>{row.label || row.planet || `${row.maha_dasa} – ${row.bukti}`}</td>
                <td>{row.start}</td>
                <td>{row.end}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  )
}

function MeaningCard({ interpretation }) {
  if (!interpretation) return null
  return (
    <article className="td-card il-meaning">
      <h4 className="td-card__title">What Indu Lagna benefits mean</h4>
      <ul className="il-list">
        {(interpretation.themes || []).map(t => (
          <li key={t} className="il-list__item">{t}</li>
        ))}
      </ul>
      <p className="td-card__hint il-disclaimer">{interpretation.disclaimer}</p>
    </article>
  )
}

function DasaTimeline({ periods }) {
  const [open, setOpen] = useState(false)
  if (!periods?.length) return null
  return (
    <section className="td-section td-section--tier3">
      <button type="button" className="td-section__toggle" onClick={() => setOpen(o => !o)}>
        <span>Full primary Dasa–Bhukti timeline ({periods.length} windows)</span>
        <span aria-hidden="true">{open ? '▾' : '▸'}</span>
      </button>
      {open && (
        <div className="il-table-wrap">
          <table className="il-table">
            <thead>
              <tr>
                <th>Mahadasha</th>
                <th>Bhukti</th>
                <th>Start</th>
                <th>End</th>
              </tr>
            </thead>
            <tbody>
              {periods.map((p, i) => (
                <tr key={`${p.start}-${i}`}>
                  <td>{p.maha_dasa}</td>
                  <td>{p.bukti}</td>
                  <td>{p.start}</td>
                  <td>{p.end}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

function FastTransitsSection({ rows }) {
  const [open, setOpen] = useState(false)
  if (!rows?.length) return null
  return (
    <section className="td-section td-section--tier3">
      <button type="button" className="td-section__toggle" onClick={() => setOpen(o => !o)}>
        <span>Minor fast-planet transits ({rows.length}) — Sun / Mercury / Moon</span>
        <span aria-hidden="true">{open ? '▾' : '▸'}</span>
      </button>
      {open && (
        <div className="il-table-wrap">
          <table className="il-table">
            <thead>
              <tr>
                <th>Transit</th>
                <th>Start</th>
                <th>End</th>
                <th>Days</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p, i) => (
                <tr key={`${p.start}-${i}`}>
                  <td>{p.label}</td>
                  <td>{p.start}</td>
                  <td>{p.end}</td>
                  <td>{p.duration_days}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default function InduLagnaPanel({ chart, userId, enabled = true }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    if (!chart || !enabled) return
    setLoading(true)
    setError('')
    api.post('/indu-lagna', chartPayload(chart, userId, { transit_years: 10 }))
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Could not load Indu Lagna.'))
      .finally(() => setLoading(false))
  }, [chart, userId, enabled])

  useEffect(() => {
    load()
  }, [load])

  if (!enabled) {
    return <div className="td-loading" style={{ opacity: 0.6 }}>Open My Chart to load Indu Lagna…</div>
  }
  if (loading && !data) {
    return <div className="td-loading">Calculating Indu Lagna…</div>
  }
  if (error) {
    return <div className="td-error" role="alert">{error}</div>
  }
  if (!data) return null

  const cur = data.current || {}
  const up = data.upcoming || {}
  const targets = (data.meta?.transit_targets || []).join(' · ')

  return (
    <div className="td-panel il-panel">
      <p className="td-panel__intro">
        Indu Lagna judges <strong>natal wealth promise</strong> (occupants, lord, aspects) and
        <strong> when it activates</strong> through Dasa/Bhukti and slow Jupiter/Saturn transits.
      </p>

      <HeroStrip hero={data.hero} summary={data.summary} />
      <NatalJudgmentCard judgment={data.natal_judgment} induLagna={data.indu_lagna} />

      <h3 className="il-layer-title">When it activates</h3>
      <div className="il-grid">
        <PeriodTable
          title="Primary — Dasa/Bhukti"
          subtitle="Indu lord or natal occupants rule Maha or Bhukti"
          rows={cur.dasa_bhukti}
          tier="primary"
          emptyText="No primary fortune Dasa/Bhukti active today."
        />
        <PeriodTable
          title="Secondary — Jupiter & Saturn"
          subtitle={`Slow transits over ${targets || 'Indu sign / lord sign'}`}
          rows={cur.slow_transits}
          tier="secondary"
          emptyText="No Jupiter/Saturn slow transit active now."
        />
      </div>
      <div className="il-grid">
        <PeriodTable
          title="Upcoming primary windows"
          rows={up.dasa_bhukti}
          tier="primary-up"
          emptyText="No upcoming primary windows in horizon."
        />
        <PeriodTable
          title="Upcoming slow transits (10 yr)"
          rows={up.slow_transits}
          tier="secondary-up"
          emptyText="No upcoming Jupiter/Saturn transits in horizon."
        />
      </div>

      <DasaTimeline periods={data.dasa_bhukti_periods} />
      <FastTransitsSection rows={data.fast_transits} />

      <MeaningCard interpretation={data.interpretation} />
    </div>
  )
}
