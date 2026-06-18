/**
 * HealthPanel — D3 Drekkana body map, Dasa/Bhukti + transit awareness (EN + TA).
 */
import { useState, useEffect, useCallback, useRef } from 'react'
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

function Bilingual({ en, ta, className = '', inline = false }) {
  if (inline) {
    return (
      <span className={className}>
        <span className="hl-bi__en hl-bi__inline">{en}</span>
        {ta && <span className="hl-bi__ta hl-bi__inline"> · {ta}</span>}
      </span>
    )
  }
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

function TagChips({ tags }) {
  if (!tags?.length) return null
  return (
    <span className="hl-tags">
      {tags.map(t => (
        <span key={t} className={`hl-tag hl-tag--${t.toLowerCase()}`}>{t}</span>
      ))}
    </span>
  )
}

function D3FactorCard({ f }) {
  const cls = RISK_CLASS[f.risk] || RISK_CLASS.moderate
  return (
    <article className={`hl-warning ${cls}`}>
      <div className="hl-warning__top">
        <Bilingual en={f.body_part_en} ta={f.body_part_ta} inline />
        <span className={`hl-risk-badge ${cls}`}>
          {RISK_LABEL[f.risk]?.en || f.risk}
        </span>
      </div>
      <p className="hl-warning__planet">
        {f.planet} · D3 H{f.d3_house} · D1 H{f.d1_house}
        <TagChips tags={f.tags} />
      </p>
      <ul className="hl-warning__reasons">
        {(f.reasons_en || []).map((r, i) => (
          <li key={`${r}-${i}`}>
            <Bilingual en={r} ta={f.reasons_ta?.[i]} inline />
          </li>
        ))}
      </ul>
    </article>
  )
}

function TextFactorList({ items }) {
  if (!items?.length) {
    return (
      <p className="td-card__hint hl-factor-empty">
        <Bilingual en="No factors in this layer." ta="இந்த அடுக்கில் காரணிகள் இல்லை." inline />
      </p>
    )
  }
  return (
    <ul className="hl-factor-list">
      {items.map((item, i) => (
        <li key={`${item.text_en}-${i}`} className="hl-factor-list__item">
          <Bilingual en={item.text_en} ta={item.text_ta} inline />
        </li>
      ))}
    </ul>
  )
}

function FactorSection({ id, titleEn, titleTa, count, defaultOpen = true, children }) {
  return (
    <details className="hl-factor-section" id={id} open={defaultOpen}>
      <summary className="hl-factor-section__summary">
        <Bilingual en={titleEn} ta={titleTa} inline />
        <span className="hl-layer-title__count">({count})</span>
      </summary>
      <div className="hl-factor-section__body">{children}</div>
    </details>
  )
}

function TransitTodayTable({ rows, date }) {
  if (!rows?.length) return null
  return (
    <div className="hl-transit-panel">
      <h3 className="hl-layer-title hl-layer-title--sub">
        <Bilingual en="Today's transits" ta="இன்றைய கோசாரம்" inline />
        <span className="hl-transit-date">as of {date}</span>
      </h3>
      <div className="hl-table-wrap">
        <table className="hl-table hl-table--transit">
          <thead>
            <tr>
              <th>Planet</th>
              <th>Sign</th>
              <th>D1 H</th>
              <th>D3 H</th>
              <th>Body / உடல்</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(row => (
              <tr
                key={row.planet}
                className={row.health_sensitive ? 'hl-table__sensitive' : ''}
              >
                <td>
                  {row.planet}
                  {row.slow && <span className="hl-slow-badge">slow</span>}
                </td>
                <td>
                  <span>{row.sign}</span>
                  {row.sign_ta && <span className="hl-bi__ta"> / {row.sign_ta}</span>}
                </td>
                <td>{row.house_d1}</td>
                <td>{row.house_d3}</td>
                <td>
                  {row.body_part_en ? (
                    <Bilingual en={row.body_part_en} ta={row.body_part_ta} inline />
                  ) : (
                    <span className="hl-muted">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function HealthPanel({ chart, userId, enabled = true }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedZone, setSelectedZone] = useState(null)
  const tableRef = useRef(null)

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

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 640px)')
    const sync = () => {
      if (tableRef.current) tableRef.current.open = mq.matches
    }
    sync()
    mq.addEventListener('change', sync)
    return () => mq.removeEventListener('change', sync)
  }, [data])

  const handleZoneSelect = (zone) => {
    setSelectedZone(zone)
    if (zone && tableRef.current) {
      tableRef.current.open = true
      tableRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }

  if (!enabled) {
    return <div className="td-loading" style={{ opacity: 0.6 }}>Open Health tab after calculating your chart…</div>
  }
  if (loading && !data) return <div className="td-loading">Computing D3 health map…</div>
  if (error) return <div className="td-error" role="alert">{error}</div>
  if (!data) return null

  const s = data.summary || {}
  const fg = data.factor_groups || {}
  const d3Natal = fg.d3_natal || []
  const dasaItems = fg.dasa || []
  const transitItems = fg.transit || []
  const totalFactors = d3Natal.length + dasaItems.length + transitItems.length
  const d3Asc = data.drekkana_ascendant || {}
  const d3Pos = data.drekkana_positions || {}
  const overallCls = RISK_CLASS[s.overall_risk] || RISK_CLASS.low

  const zoneDetail = selectedZone
    ? (data.body_regions || []).find(r => r.zone === selectedZone)
    : null

  const highlightedPlanets = selectedZone
    ? new Set(
        (data.planet_rows || [])
          .filter(r => r.body_zone === selectedZone)
          .map(r => r.planet),
      )
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
          <Bilingual en="Lagna body" ta="லக்ன உடல் பகுதி" inline />:{' '}
          <strong>{s.lagna_body_en}</strong> / {s.lagna_body_ta}
        </p>
        <p className="hl-hero__meta">
          <Bilingual en="Dasa" ta="தசை" inline />: <strong>{s.maha_dasa}–{s.bhukti}</strong>
          <span className="hl-hero__dates"> ({s.dasa_period})</span>
        </p>
      </div>

      <TransitTodayTable rows={data.transit_today} date={s.transit_date} />

      <div className="hl-charts-grid">
        <div className="hl-chart-card">
          <h4 className="hl-chart-card__title">
            <Bilingual en="Body map (D3)" ta="உடல் வரைபடம் (D3)" />
          </h4>
          <BodyMapSvg
            regions={data.body_regions}
            selectedZone={selectedZone}
            onSelectZone={handleZoneSelect}
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
        <Bilingual en="Awareness factors" ta="விழிப்பு காரணிகள்" inline />
        <span className="hl-layer-title__count">({totalFactors})</span>
      </h3>

      {totalFactors === 0 ? (
        <p className="td-card__hint">
          <Bilingual
            en="No strong D3 health-house triggers today. Stay mindful of routine wellness."
            ta="இன்று வலுவான D3 ஆரோக்கிய வீடு சுட்டிக்காட்டுதல்கள் இல்லை."
            inline
          />
        </p>
      ) : (
        <div className="hl-factor-groups">
          <FactorSection
            id="hl-d3-natal"
            titleEn="D3 natal"
            titleTa="D3 ஜாதகம்"
            count={d3Natal.length}
            defaultOpen
          >
            {d3Natal.length === 0 ? (
              <TextFactorList items={[]} />
            ) : (
              <div className="hl-warnings">
                {d3Natal.map(f => (
                  <D3FactorCard key={`${f.planet}-${f.d3_house}`} f={f} />
                ))}
              </div>
            )}
          </FactorSection>

          <FactorSection
            id="hl-dasa"
            titleEn="Dasa / Bhukti"
            titleTa="தசை / புத்தி"
            count={dasaItems.length}
            defaultOpen={dasaItems.length > 0}
          >
            <TextFactorList items={dasaItems} />
          </FactorSection>

          <FactorSection
            id="hl-transit"
            titleEn="Transits"
            titleTa="கோசாரம்"
            count={transitItems.length}
            defaultOpen={transitItems.length > 0}
          >
            <TextFactorList items={transitItems} />
          </FactorSection>
        </div>
      )}

      <details className="hl-table-collapse" ref={tableRef}>
        <summary className="hl-layer-title hl-table-collapse__summary">
          <Bilingual en="D3 body-part table" ta="D3 உடல் பகுதி அட்டவணை" inline />
          <span className="hl-layer-title__count">({(data.planet_rows || []).length})</span>
        </summary>
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
              {(data.planet_rows || []).map(row => {
                const highlight = highlightedPlanets?.has(row.planet)
                return (
                  <tr
                    key={row.planet}
                    className={[
                      row.health_house_d3 ? 'hl-table__sensitive' : '',
                      highlight ? 'hl-table__highlight' : '',
                    ].filter(Boolean).join(' ')}
                  >
                    <td>{row.planet}</td>
                    <td>{row.d1_house}</td>
                    <td>{row.d3_house}</td>
                    <td>{row.body_part_en}</td>
                    <td>{row.body_part_ta}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  )
}
