/**
 * TamilDoshasPanel — natal predictive doshas dashboard (My Chart section).
 */
import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'

const CONFIDENCE_CLASS = {
  HIGH: 'td-confidence--high',
  MEDIUM: 'td-confidence--medium',
  'MEDIUM-HIGH': 'td-confidence--medium-high',
  LOW: 'td-confidence--low',
  UNVERIFIED: 'td-confidence--unverified',
}

function ConfidenceBadge({ level }) {
  if (!level) return null
  return (
    <span className={`td-confidence ${CONFIDENCE_CLASS[level] || 'td-confidence--low'}`}>
      {level}
    </span>
  )
}

function SourceNote({ text }) {
  if (!text) return null
  return <p className="td-source-note">{text}</p>
}

function SummaryStrip({ summary }) {
  if (!summary) return null
  return (
    <div className="td-summary" role="list">
      <div className="td-summary__item" role="listitem">
        <span className="td-summary__label">Dagdha signs</span>
        <span className="td-summary__value">{summary.dagdha_count ?? 0}</span>
      </div>
      <div className="td-summary__item" role="listitem">
        <span className="td-summary__label">Yogi graha</span>
        <span className="td-summary__value">{summary.yogi_graha ?? '—'}</span>
      </div>
      <div className="td-summary__item" role="listitem">
        <span className="td-summary__label">Vadhai zone</span>
        <span className="td-summary__value">{summary.vadhai_nakshatra ?? '—'}</span>
      </div>
      <div className="td-summary__item" role="listitem">
        <span className="td-summary__label">Vainasikam</span>
        <span className="td-summary__value">{summary.vainasikam_nakshatra ?? '—'}</span>
      </div>
    </div>
  )
}

function ThithiCard({ data, shashtiVariant, onShashtiChange }) {
  if (!data) return null
  const dagdha = (data.dagdha_rasis || []).map(r => r.name).join(', ') || 'None (exempt)'
  const houses = (data.affected_houses || []).join(', ')
  return (
    <article className="td-card td-card--tier1">
      <header className="td-card__head">
        <h4 className="td-card__title">Thithi Soonyam (Dagdha Rasi)</h4>
        <ConfidenceBadge level={data.confidence} />
      </header>
      <p className="td-card__line">
        <strong>Tithi:</strong> {data.tithi_name} ({data.paksha}) · index {data.tithi_index}
      </p>
      <p className="td-card__line">
        <strong>Dagdha signs:</strong> {dagdha}
      </p>
      <p className="td-card__line">
        <strong>Houses from Lagna:</strong> {houses || '—'}
      </p>
      {data.planets_in_dagdha?.length > 0 && (
        <p className="td-card__warn">
          Planets in dagdha: {data.planets_in_dagdha.map(p => `${p.planet} (H${p.house})`).join(', ')}
        </p>
      )}
      {data.tithi_index === 6 && (
        <div className="td-shashti-toggle">
          <span className="td-shashti-toggle__label">Shashti lineage variant:</span>
          <label className="td-shashti-option">
            <input
              type="radio"
              name="shashti"
              checked={shashtiVariant === 'mesha_simha'}
              onChange={() => onShashtiChange('mesha_simha')}
            />
            Mesha + Simha
          </label>
          <label className="td-shashti-option">
            <input
              type="radio"
              name="shashti"
              checked={shashtiVariant === 'mesha_kataka'}
              onChange={() => onShashtiChange('mesha_kataka')}
            />
            Mesha + Kataka
          </label>
        </div>
      )}
      <SourceNote text={data.source_note} />
    </article>
  )
}

function YogiCard({ data }) {
  if (!data) return null
  return (
    <article className="td-card td-card--tier1">
      <header className="td-card__head">
        <h4 className="td-card__title">Yogi / Ava Yogi</h4>
        <ConfidenceBadge level={data.confidence} />
      </header>
      <p className="td-card__line">
        <strong>Yogi graha:</strong> {data.yogi_graha}
        {' · '}
        <strong>Duplicate:</strong> {data.duplicate_yogi_graha}
      </p>
      <p className="td-card__line">
        <strong>Yogi point:</strong> {data.yogi_point?.nakshatra} ({data.yogi_point?.rasi})
      </p>
      <p className="td-card__line">
        <strong>Avayogi graha:</strong> {data.avayogi_graha}
        {' · '}
        <strong>Point:</strong> {data.avayogi_point?.nakshatra} ({data.avayogi_point?.rasi})
      </p>
      <SourceNote text={data.source_note} />
    </article>
  )
}

function RedZonesCard({ data }) {
  if (!data) return null
  return (
    <article className="td-card td-card--tier1">
      <header className="td-card__head">
        <h4 className="td-card__title">Vadhai &amp; Vainasikam (natal red zones)</h4>
        <ConfidenceBadge level={data.confidence} />
      </header>
      <p className="td-card__line">
        <strong>Janma nakshatra:</strong> {data.janma_nakshatra?.name}
      </p>
      <p className="td-card__line">
        <strong>Vadhai (7th):</strong> {data.vadhai?.name} — lord {data.vadhai?.lord}
      </p>
      <p className="td-card__line">
        <strong>Vainasikam (22nd):</strong> {data.vainasikam?.name} — lord {data.vainasikam?.lord}
      </p>
      <p className="td-card__hint">
        Malefic when transiting planets pass through these nakshatras (not a partner check).
      </p>
      <SourceNote text={data.source_note} />
    </article>
  )
}

function MudakkuMethod({ method }) {
  if (!method) return null
  const isUnverified = method.confidence === 'UNVERIFIED'
  return (
    <div className={`td-mudakku-method${isUnverified ? ' td-mudakku-method--muted' : ''}`}>
      <header className="td-card__head">
        <h5 className="td-card__subtitle">{method.label}</h5>
        <ConfidenceBadge level={method.confidence} />
      </header>
      <p className="td-card__line">
        <strong>Result:</strong> {method.rasi?.name} ({method.rasi?.english}) · House {method.house}
      </p>
      {method.nakshatra && (
        <p className="td-card__line">
          <strong>Nakshatra:</strong> {method.nakshatra.name} · pada {method.pada}
        </p>
      )}
      <p className="td-card__how">{method.how_calculated}</p>
      <SourceNote text={method.source_note} />
    </div>
  )
}

function MudakkuSection({ data }) {
  const [open, setOpen] = useState(false)
  if (!data) return null
  return (
    <section className="td-section td-section--tier3">
      <button type="button" className="td-section__toggle" onClick={() => setOpen(o => !o)}>
        <span>Mudakku Rasi — two methods (do not merge)</span>
        <span aria-hidden="true">{open ? '▾' : '▸'}</span>
      </button>
      {data.methods_disagree && (
        <p className="td-card__warn td-section__note">Methods A and B disagree — show both.</p>
      )}
      {open && (
        <div className="td-mudakku-grid">
          <MudakkuMethod method={data.method_a} />
          <MudakkuMethod method={data.method_b} />
        </div>
      )}
    </section>
  )
}

export default function TamilDoshasPanel({ chart, userId, enabled = true }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [shashtiVariant, setShashtiVariant] = useState('mesha_simha')

  const load = useCallback((variant) => {
    if (!chart || !enabled) return
    setLoading(true)
    setError('')
    api.post('/tamil-doshas', chartPayload(chart, userId, { shashti_variant: variant }))
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Could not load Tamil doshas.'))
      .finally(() => setLoading(false))
  }, [chart, userId, enabled])

  useEffect(() => {
    load(shashtiVariant)
  }, [load, shashtiVariant])

  const handleShashtiChange = (variant) => {
    setShashtiVariant(variant)
  }

  if (!enabled) {
    return <div className="td-loading" style={{ opacity: 0.6 }}>Open My Chart to load Tamil doshas…</div>
  }
  if (loading && !data) {
    return <div className="td-loading">Calculating Tamil doshas…</div>
  }
  if (error) {
    return <div className="td-error" role="alert">{error}</div>
  }
  if (!data) return null

  return (
    <div className="td-panel">
      <p className="td-panel__intro">
        Natal obstruction &amp; prosperity markers from Tamil predictive tradition.
        Confidence tags reflect source-audit strength — not all rules carry equal authority.
      </p>
      <SummaryStrip summary={data.summary} />
      <div className="td-tier">
        <h3 className="td-tier__heading">Well attested</h3>
        <ThithiCard
          data={data.thithi_soonyam}
          shashtiVariant={shashtiVariant}
          onShashtiChange={handleShashtiChange}
        />
        <YogiCard data={data.yogi} />
        <RedZonesCard data={data.red_zones} />
      </div>
      <MudakkuSection data={data.mudakku} />
    </div>
  )
}
