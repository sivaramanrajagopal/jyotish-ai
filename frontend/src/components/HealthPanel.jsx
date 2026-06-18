/**
 * HealthPanel — D3 Drekkana body map, Dasa/Bhukti + transit awareness (EN + TA).
 */
import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'
import SouthIndianChart from './SouthIndianChart'
import BodyMapSvg from './BodyMapSvg'

const RISK_CLASS = {
  low: 'hl-risk--low',
  moderate: 'hl-risk--moderate',
  high: 'hl-risk--high',
}

const RISK_LABEL = {
  low: { en: 'Low awareness', ta: 'குறைந்த விழிப்பு' },
  moderate: { en: 'Moderate', ta: 'மிதமான' },
  high: { en: 'Higher awareness', ta: 'அதிக விழிப்பு' },
}

function Bilingual({ en, ta, className = '' }) {
  return (
    <span className={className}>
      <span className="hl-bi__en">{en}</span>
      {ta && <span className="hl-bi__ta">{ta}</span>}
    </span>
  )
}

function Disclaimer({ text }) {
  if (!text?.en) return null
  return (
    <div className="hl-disclaimer" role="alert">
      <strong>⚠️ {text.en}</strong>
      <p className="hl-disclaimer__ta">{text.ta}</p>
    </div>
  )
}

function WarningCard({ w }) {
  const cls = RISK_CLASS[w.risk] || RISK_CLASS.moderate
  return (
    <article className={`hl-warning ${cls}`}>
      <div className="hl-warning__top">
        <Bilingual en={w.body_part_en} ta={w.body_part_ta} />
        <span className={`hl-risk-badge ${cls}`}>
          {RISK_LABEL[w.risk]?.en || w.risk}
        </span>
      </div>
      {w.planet && (
        <p className="hl-warning__planet">
          {w.planet}
          {w.d3_house ? ` · D3 H${w.d3_house}` : ''}
        </p>
      )}
      <ul className="hl-warning__reasons">
        {(w.reasons_en || []).map((r, i) => (
          <li key={`${r}-${i}`}>
            <span>{r}</span>
            {w.reasons_ta?.[i] && <span className="hl-bi__ta"> — {w.reasons_ta[i]}</span>}
          </li>
        ))}
      </ul>
    </article>
  )
}

export default function HealthPanel({ chart, userId, enabled = true }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedZone, setSelectedZone] = useState(null)

  const load = useCallback(() => {
    if (!chart || !enabled) return
    setLoading(true)
    setError('')
    api.post('/health/analyze', chartPayload(chart, userId))
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Could not load health analysis.'))
      .finally(() => setLoading(false))
  }, [chart, userId, enabled])

  useEffect(() => { load() }, [load])

  if (!enabled) {
    return <div className="td-loading" style={{ opacity: 0.6 }}>Open Health tab after calculating your chart…</div>
  }
  if (loading && !data) return <div className="td-loading">Computing D3 health map…</div>
  if (error) return <div className="td-error" role="alert">{error}</div>
  if (!data) return null

  const s = data.summary || {}
  const d3Asc = data.drekkana_ascendant || {}
  const d3Pos = data.drekkana_positions || {}
  const overallCls = RISK_CLASS[s.overall_risk] || RISK_CLASS.low

  const zoneDetail = selectedZone
    ? (data.body_regions || []).find(r => r.zone === selectedZone)
    : null

  return (
    <div className="td-panel hl-panel">
      <Disclaimer text={data.disclaimer} />

      <div className="hl-hero">
        <div className="hl-hero__top">
          <span className="hl-hero__label">
            <Bilingual en="Health awareness" ta="ஆரோக்கிய விழிப்பு" />
          </span>
          <span className={`hl-risk-badge ${overallCls}`}>
            {RISK_LABEL[s.overall_risk]?.en} / {RISK_LABEL[s.overall_risk]?.ta}
          </span>
        </div>
        <p className="hl-hero__headline">
          <Bilingual en={data.hero?.headline_en} ta={data.hero?.headline_ta} />
        </p>
        <p className="hl-hero__meta">
          D3 Lagna <strong>{s.d3_lagna}</strong> ({s.d3_lagna_ta}) ·{' '}
          <Bilingual en="Lagna body" ta="லக்ன உடல் பகுதி" />:{' '}
          <strong>{s.lagna_body_en}</strong> / {s.lagna_body_ta}
        </p>
        <p className="hl-hero__meta">
          <Bilingual en="Dasa" ta="தசை" />: <strong>{s.maha_dasa}–{s.bhukti}</strong>
          <span className="hl-hero__dates"> ({s.dasa_period})</span>
        </p>
      </div>

      <div className="hl-charts-grid">
        <div className="hl-chart-card">
          <h4 className="hl-chart-card__title">
            <Bilingual en="Body map (D3)" ta="உடல் வரைபடம் (D3)" />
          </h4>
          <BodyMapSvg
            regions={data.body_regions}
            selectedZone={selectedZone}
            onSelectZone={setSelectedZone}
          />
          <div className="hl-legend">
            <span className="hl-legend__item hl-risk--low">Low / குறைவு</span>
            <span className="hl-legend__item hl-risk--moderate">Moderate / மிதம்</span>
            <span className="hl-legend__item hl-risk--high">Higher / அதிகம்</span>
          </div>
          {zoneDetail && (
            <p className="hl-zone-detail">
              <strong>{zoneDetail.label_en}</strong> / {zoneDetail.label_ta}
              {' — '}{zoneDetail.score} pts
            </p>
          )}
        </div>
        <div className="hl-chart-card">
          <h4 className="hl-chart-card__title">
            <Bilingual en="D3 — Drekkana chart" ta="D3 — திரேக்கானம்" />
          </h4>
          <SouthIndianChart
            title="D3"
            subtitle={`Lagna: ${d3Asc.sign || '—'}`}
            planetPositions={d3Pos}
            lagnaSignIndex={d3Asc.sign_index}
            drekkana
            variant="classic"
            showDetails
            chartKind="natal"
          />
        </div>
      </div>

      <h3 className="hl-layer-title">
        <Bilingual en="Awareness notes" ta="விழிப்பு குறிப்புகள்" />
        <span className="hl-layer-title__count">({data.warnings?.length || 0})</span>
      </h3>
      <div className="hl-warnings">
        {(data.warnings || []).length === 0 ? (
          <p className="td-card__hint">
            <Bilingual
              en="No strong D3 health-house triggers today. Stay mindful of routine wellness."
              ta="இன்று வலுவான D3 ஆரோக்கிய வீடு சுட்டிக்காட்டுதல்கள் இல்லை."
            />
          </p>
        ) : (
          data.warnings.map((w, i) => <WarningCard key={`${w.body_part_en}-${i}`} w={w} />)
        )}
      </div>

      <h3 className="hl-layer-title">
        <Bilingual en="D3 body-part table" ta="D3 உடல் பகுதி அட்டவணை" />
      </h3>
      <div className="hl-table-wrap">
        <table className="hl-table">
          <thead>
            <tr>
              <th>Planet / கிரகம்</th>
              <th>D1 H</th>
              <th>D3 H</th>
              <th>Body EN</th>
              <th>உடல் பகுதி</th>
            </tr>
          </thead>
          <tbody>
            {(data.planet_rows || []).map(row => (
              <tr key={row.planet} className={row.health_house_d3 ? 'hl-table__sensitive' : ''}>
                <td>{row.planet}</td>
                <td>{row.d1_house}</td>
                <td>{row.d3_house}</td>
                <td>{row.body_part_en}</td>
                <td>{row.body_part_ta}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
