/**
 * HealthPanel — D3 Drekkana body map, Dasa/Bhukti + transit awareness (EN + TA).
 */
import { useState, useEffect, useMemo, useRef } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'
import SouthIndianChart from './SouthIndianChart'
import BodyMapSvg from './BodyMapSvg'
import BhavatBhavamLayer from './BhavatBhavamLayer'
import { HouseStatusDetail, HouseStatusTiles } from './TransitHouseStatus'

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

function HealthHousesPrimer() {
  return (
    <details className="hl-primer">
      <summary className="hl-primer__summary">
        <Bilingual
          en="What are D3 health houses (6, 8, 12)?"
          ta="D3 ஆரோக்கிய வீடுகள் (6, 8, 12) என்றால்?"
          inline
        />
      </summary>
      <p className="hl-primer__body">
        <Bilingual
          en="In the D3 Drekkana chart, houses 6, 8, and 12 are dusthana (challenging) zones linked to vitality and recovery. Planets here — especially malefics — raise awareness for the mapped body part. Colors on the map reflect combined natal, Dasa, and transit scores, for awareness only."
          ta="D3 திரேக்கான வரைபடத்தில் 6, 8, 12ம் வீடுகள் துஷ்ட வீடுகள் — உடல் நிலை மற்றும் குணமடைதலுடன் தொடர்புடையவை. இங்குள்ள கிரகங்கள் — குறிப்பாக பாப கிரகங்கள் — உடல் பகுதிக்கு விழிப்புணர்வை உயர்த்தும். வரைபட நிறங்கள் ஜாதகம், தசை, கோசார மதிப்பெண்களின் தொகை; விழிப்புணர்வுக்காக மட்டும்."
          inline
        />
      </p>
    </details>
  )
}

function ZoneRationale({ region, labelPrefix }) {
  if (!region?.rationale_en) return null
  const prefix = labelPrefix || region.label_en
  return (
    <p className="hl-zone-rationale">
      <strong>{prefix}</strong>
      {' — '}
      <Bilingual en={region.rationale_en} ta={region.rationale_ta} inline />
    </p>
  )
}

function HouseBadge({ house, kind }) {
  const health = kind === '1' ? [1, 6, 8, 12] : [6, 8, 12]
  if (!health.includes(house)) return house
  return (
    <span className="hl-house-badge" title={`D${kind} health house`}>
      {house}
      <span className="hl-house-badge__dot" aria-hidden>●</span>
    </span>
  )
}

function LiveMarks({ dasa, transit }) {
  return (
    <>
      {dasa && (
        <abbr className="hl-live-mark" title="Current Dasa or Bhukti">★</abbr>
      )}
      {transit && (
        <abbr className="hl-live-mark hl-live-mark--transit" title="Current transit">*</abbr>
      )}
    </>
  )
}

const TAMIL_ZONE_LABELS = {
  head: { en: 'Head / face', ta: 'தலை / முகம்', emoji: '👤' },
  neck: { en: 'Neck', ta: 'கழுத்து', emoji: '🦴' },
  chest: { en: 'Chest', ta: 'மார்பு', emoji: '🫀' },
  torso: { en: 'Torso / ribs', ta: 'விலா / முதுகு', emoji: '🫁' },
  abdomen: { en: 'Abdomen', ta: 'வயிறு', emoji: '🟠' },
  arms: { en: 'Arms / shoulders', ta: 'கை / தோள்', emoji: '💪' },
  pelvis: { en: 'Pelvis / reproductive', ta: 'இடுப்பு / இனப்பெருக்க உறுப்பு', emoji: '🟣' },
  legs: { en: 'Legs / knees / feet', ta: 'கால் / முழங்கால் / பாதம்', emoji: '🦵' },
}

function tamilRisk(score) {
  if (score >= 6) return 'high'
  if (score >= 3) return 'moderate'
  return 'low'
}

function tamilRegionsFromRows(rows) {
  const grouped = {}
  for (const row of rows || []) {
    const zone = row.tamil_d3_zone
    if (!zone) continue
    if (!grouped[zone]) grouped[zone] = { score: 0, planets: [] }
    let score = 0
    if (row.health_house_d3) score += 2
    if (row.malefic && row.health_house_d3) score += 2
    if (row.malefic) score += 0.5
    if (row.live_dasa) score += 2
    if (row.live_transit) score += 2
    grouped[zone].score += score
    grouped[zone].planets.push(row)
  }
  return Object.entries(grouped)
    .map(([zone, group]) => {
      const labels = TAMIL_ZONE_LABELS[zone] || { en: zone, ta: zone, emoji: '' }
      return {
        zone,
        score: group.score,
        risk: tamilRisk(group.score),
        label_en: labels.en,
        label_ta: labels.ta,
        emoji: labels.emoji,
        planets: group.planets,
      }
    })
    .sort((a, b) => b.score - a.score)
}

function TamilD3BodyMap({ rows }) {
  const [selectedZone, setSelectedZone] = useState(null)
  const regions = useMemo(() => tamilRegionsFromRows(rows), [rows])
  if (!regions.length) return null

  const liveCount = (rows || []).filter((row) => row.live_dasa || row.live_transit).length
  const picked = selectedZone
    ? regions.find((region) => region.zone === selectedZone)
    : regions[0]

  const toggleZone = (zone) => {
    setSelectedZone((current) => (current === zone ? null : zone))
  }

  return (
    <details className="hl-table-collapse hl-tamil-body">
      <summary className="hl-layer-title hl-table-collapse__summary">
        <Bilingual
          en="Tamil D3 body map"
          ta="தமிழ் D3 உடல் வரைபடம்"
          inline
        />
        <span className="hl-layer-title__count">({liveCount} live)</span>
      </summary>
      <p className="hl-primer__body hl-map-compare__note">
        <Bilingual
          en="Silhouette from the earlier Tamil D3 house and the planet’s own 10° slice. Color follows D3 health houses plus ★ Dasa/Bhukti and * current D3 transit. Tap a region. The map above stays on Brihat Jataka 5.25."
          ta="பழைய தமிழ் D3 வீடு + கிரகத்தின் 10° பகுதி. நிறம் D3 ஆரோக்கிய வீடுகள், ★ தசை/புத்தி, * நடப்பு D3 கோசாரம். பகுதியைத் தொடவும். மேலே உள்ள வரைபடம் பிருஹத் ஜாதகம் 5.25."
          inline
        />
      </p>
      <div className="hl-tamil-body__grid">
        <div className="hl-tamil-body__map">
          <BodyMapSvg
            regions={regions}
            selectedZone={selectedZone}
            onSelectZone={toggleZone}
          />
          <div className="hl-legend">
            <span className="hl-legend__item hl-risk--low">Low / குறைவு</span>
            <span className="hl-legend__item hl-risk--moderate">Moderate / மிதம்</span>
            <span className="hl-legend__item hl-risk--high">Higher / அதிகம்</span>
          </div>
        </div>
        <ul className="hl-tamil-body__zones">
          {regions.map((region) => {
            const active = selectedZone === region.zone
            return (
              <li
                key={region.zone}
                className={`hl-tamil-body__zone${active ? ' hl-tamil-body__zone--active' : ''}`}
              >
                <button
                  type="button"
                  className="hl-tamil-body__zone-btn"
                  aria-pressed={active}
                  onClick={() => toggleZone(region.zone)}
                >
                  <span className="hl-tamil-body__zone-label">
                    {region.emoji ? `${region.emoji} ` : ''}
                    {region.label_en}
                  </span>
                  {region.label_ta && (
                    <span className="hl-bi__ta"> / {region.label_ta}</span>
                  )}
                </button>
                <div className="hl-tamil-body__planets">
                  {region.planets.map((row) => (
                    <span key={row.planet} className="hl-tamil-body__chip">
                      {row.planet} · {row.tamil_d3_en}
                      <LiveMarks dasa={row.live_dasa} transit={row.live_transit} />
                    </span>
                  ))}
                </div>
              </li>
            )
          })}
        </ul>
      </div>
      {picked && (
        <p className="hl-zone-rationale hl-tamil-body__rationale">
          <strong>
            {picked.emoji ? `${picked.emoji} ` : ''}
            {picked.label_en}
            {selectedZone ? ' (selected)' : ' (highest score)'}
          </strong>
          {' — '}
          {picked.planets.map((row) => row.planet).join(', ')}
        </p>
      )}
    </details>
  )
}

function MapCompareTable({ rows }) {
  if (!rows?.length) return null
  const agreeCount = rows.filter((row) => row.maps_agree).length
  return (
    <details className="hl-table-collapse hl-map-compare">
      <summary className="hl-layer-title hl-table-collapse__summary">
        <Bilingual
          en="Earlier D3 house map (reference)"
          ta="முந்தைய D3 வீட்டு வரைபடம் (ஒப்பீடு)"
          inline
        />
        <span className="hl-layer-title__count">
          ({agreeCount}/{rows.length} same region)
        </span>
      </summary>
      <p className="hl-primer__body hl-map-compare__note">
        <Bilingual
          en="Tamil drekkana used the planet’s D3 house and its own 10° slice. Brihat Jataka 5.25 uses the house from the birth lagna and one column from the lagna’s rising decan. Bold rows share a body region. On both columns, ★ is the running Dasa/Bhukti and * is a current health transit (Tamil by D3 house, Brihat Jataka by D1 house). The map and factors above stay on Brihat Jataka."
          ta="பழைய வரைபடம் கிரகத்தின் D3 வீட்டையும் அதன் 10° பகுதியையும் பயன்படுத்தியது. பிருஹத் ஜாதகம் 5.25 பிறப்பு லக்ன வீட்டையும் லக்ன திரேக்கானத்தையும் பயன்படுத்துகிறது. தடித்த வரிகள் ஒரே உடல் பகுதி. இரு நெடுவரிசைகளிலும் ★ நடப்பு தசை/புத்தி, * இன்றைய ஆரோக்கிய கோசாரம் (தமிழ் D3 வீடு, பிருஹத் ஜாதகம் D1 வீடு). மேலே உள்ள வரைபடம் பிருஹத் ஜாதகமே."
          inline
        />
      </p>
      <div className="hl-table-wrap">
        <table className="hl-table hl-table--compare">
          <thead>
            <tr>
              <th>Planet</th>
              <th>Tamil D3 house</th>
              <th>Brihat Jataka 5.25</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const agree = Boolean(row.maps_agree)
              const emoji = agree
                ? (row.body_emoji || row.tamil_d3_emoji || '')
                : `${row.tamil_d3_emoji || ''} ${row.body_emoji || ''}`.trim()
              return (
                <tr
                  key={row.planet}
                  className={agree ? 'hl-map-compare__agree' : ''}
                >
                  <td>
                    <span className="hl-map-compare__planet">{row.planet}</span>
                    {agree && (
                      <span className="hl-map-compare__badge" title="Same body region">
                        {emoji} same region
                      </span>
                    )}
                    {!agree && emoji && (
                      <span className="hl-map-compare__split" aria-hidden>{emoji}</span>
                    )}
                  </td>
                  <td>
                    <span className={agree ? 'hl-map-compare__part' : ''}>
                      {row.tamil_d3_emoji ? `${row.tamil_d3_emoji} ` : ''}
                      {row.tamil_d3_en}
                    </span>
                    <LiveMarks dasa={row.live_dasa} transit={row.live_transit} />
                    {row.tamil_d3_ta && (
                      <span className="hl-bi__ta"> / {row.tamil_d3_ta}</span>
                    )}
                  </td>
                  <td>
                    <span className={agree ? 'hl-map-compare__part' : ''}>
                      {row.body_emoji ? `${row.body_emoji} ` : ''}
                      {row.body_part_en}
                    </span>
                    <LiveMarks dasa={row.live_dasa} transit={row.live_transit_bj} />
                    {row.body_part_ta && (
                      <span className="hl-bi__ta"> / {row.body_part_ta}</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </details>
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

function D3FactorCard({ f, id }) {
  const cls = RISK_CLASS[f.risk] || RISK_CLASS.moderate
  return (
    <article id={id} className={`hl-warning ${cls}`}>
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
  const [open, setOpen] = useState(defaultOpen)
  return (
    <details className="hl-factor-section" id={id} open={open} onToggle={e => setOpen(e.currentTarget.open)}>
      <summary className="hl-factor-section__summary">
        <Bilingual en={titleEn} ta={titleTa} inline />
        <span className="hl-layer-title__count">({count})</span>
      </summary>
      <div className="hl-factor-section__body">{children}</div>
    </details>
  )
}

/** House Links status of the 1st, 6th, 8th and 12th — the same reading as Gochar and Forecast. */
function HealthHouseLinks({ links }) {
  const [selected, setSelected] = useState(null)
  if (!links?.houses?.length) return null
  const row = links.houses.find(r => r.house === selected)
  return (
    <section className="hl-now" aria-label="Health houses on House Links">
      <h3 className="hl-section-title">
        <Bilingual en="Health houses now (House Links)" ta="ஆரோக்கிய வீடுகள் இப்போது (வீட்டுத் தொடர்பு)" inline />
      </h3>
      <p className="hl-now__line">
        <Bilingual
          en="1st body, 6th illness, 8th chronic conditions, 12th hospital and rest. Same status as Gochar and Forecast."
          ta="1 உடல், 6 நோய், 8 நாள்பட்ட நிலை, 12 மருத்துவமனை / ஓய்வு. கோசாரம், முன்னறிவிப்பு போலவே."
          inline
        />
      </p>
      <HouseStatusTiles houses={links.houses} selected={selected} onSelect={setSelected} />
      <HouseStatusDetail row={row} planets={links.planets} onClose={() => setSelected(null)} />
    </section>
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
  const [result, setResult] = useState({ chart: null, userId: null, data: null, error: '' })
  const [zonePick, setZonePick] = useState({ chart: null, zone: null })
  const tableRef = useRef(null)
  const factorsRef = useRef(null)
  const selectedZone = zonePick.chart === chart ? zonePick.zone : null
  const setSelectedZone = (zone) => setZonePick({ chart, zone })

  useEffect(() => {
    if (!chart || !enabled) return undefined
    let cancel = false
    api.post('/health/analyze', chartPayload(chart, userId))
      .then(r => {
        if (!cancel) setResult({ chart, userId, data: r.data, error: '' })
      })
      .catch(e => {
        if (cancel) return
        const detail = e.response?.data?.detail
        const message = typeof detail === 'string' ? detail : 'Could not load health analysis.'
        setResult({ chart, userId, data: null, error: message })
      })
    return () => { cancel = true }
  }, [chart, userId, enabled])

  const current = result.chart === chart && result.userId === userId
  const loading = Boolean(chart && enabled && !current)
  const data = current ? result.data : null
  const error = current ? result.error : ''

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
    const factor = (data?.factor_groups?.d3_natal || []).find(f => f.body_zone === zone)
    if (factor) {
      const el = document.getElementById(`hl-factor-${factor.planet}`)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
        el.classList.add('hl-warning--pulse')
        window.setTimeout(() => el.classList.remove('hl-warning--pulse'), 1600)
      } else if (factorsRef.current) {
        factorsRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      }
    } else if (tableRef.current) {
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

  const topRegion = (data.body_regions || [])[0] || null
  const displayRegion = zoneDetail || topRegion

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
          <Bilingual en="Lagna body (chart anchor)" ta="லக்ன உடல் (அடிப்படை)" inline />:{' '}
          <strong>{s.lagna_body_en}</strong> / {s.lagna_body_ta}
        </p>
        <p className="hl-hero__meta">
          <Bilingual en="Dasa" ta="தசை" inline />: <strong>{s.maha_dasa}–{s.bhukti}</strong>
          <span className="hl-hero__dates"> ({s.dasa_period})</span>
        </p>
      </div>

      <HealthHouseLinks links={data.house_links} />

      <TransitTodayTable rows={data.transit_today} date={s.transit_date} />

      <HealthHousesPrimer />

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
          {displayRegion && (
            <ZoneRationale
              region={displayRegion}
              labelPrefix={
                selectedZone
                  ? `${displayRegion.label_en} (selected)`
                  : `${displayRegion.label_en} (highest score)`
              }
            />
          )}
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
        <div className="hl-factor-groups" ref={factorsRef}>
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
                  <D3FactorCard
                    key={`${f.planet}-${f.d3_house}`}
                    id={`hl-factor-${f.planet}`}
                    f={f}
                  />
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

      <BhavatBhavamLayer data={data.bhavat_bhavam} variant="health" />

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
                <th>D3 H <span className="hl-col-hint" title="● = health house 6/8/12">●</span></th>
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
                      row.health_house_d3 || row.health_house_d1 ? 'hl-table__sensitive' : '',
                      highlight ? 'hl-table__highlight' : '',
                    ].filter(Boolean).join(' ')}
                  >
                    <td>
                      {row.planet}
                      {row.health_house_d3 && (
                        <span className="hl-row-badge" title="D3 health house">D3</span>
                      )}
                      {row.health_house_d1 && (
                        <span className="hl-row-badge hl-row-badge--d1" title="D1 health house">D1</span>
                      )}
                    </td>
                    <td><HouseBadge house={row.d1_house} kind="1" /></td>
                    <td><HouseBadge house={row.d3_house} kind="3" /></td>
                    <td>{row.body_part_en}</td>
                    <td>{row.body_part_ta}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </details>

      <MapCompareTable rows={data.planet_rows} />
      <TamilD3BodyMap rows={data.planet_rows} />
    </div>
  )
}
