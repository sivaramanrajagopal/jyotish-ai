/**
 * Native card — who, birth panchanga, three lords, and the open period.
 */
import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'
import { buildNativeDashboard, formatHotspotValue, formatTriggerItem, natalGandanta, transitGandanta } from '../lib/nativeDashboard'
import { resolvePanchangamLocation } from '../lib/resolveLocation'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function formatBirthDate(iso) {
  if (!iso) return ''
  const [year, month, day] = String(iso).split('-').map(Number)
  if (!year || !month || !day) return String(iso)
  return `${day} ${MONTHS[month - 1]} ${year}`
}

function withStar(planet, star) {
  if (!planet) return ''
  return star ? `${planet} (${star})` : planet
}

function pointLine(points) {
  if (!points?.length) return 'None'
  return points.map((point) => `${point.planet} · house ${point.house}`).join(', ')
}

function pointJunctions(points) {
  if (!points?.length) return ''
  return [...new Set(points.map((point) => point.junction))].join(', ')
}

function Fact({ label, value, sub, hot = false, wide = false }) {
  if (!value) return null
  return (
    <div
      className={wide ? 'col-span-2 sm:col-span-3' : undefined}
      style={{
        background: hot ? 'rgba(231, 76, 60, 0.12)' : 'var(--highlight-bg)',
        border: hot ? '2px solid #e74c3c' : '1px solid var(--card-border)',
        borderRadius: '0.65rem',
        padding: '0.65rem 0.75rem',
        minWidth: 0,
      }}
    >
      <div style={{ fontSize: '0.68rem', letterSpacing: '0.04em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
        {label}
      </div>
      <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.15rem', overflowWrap: 'break-word' }}>{value}</div>
      {sub ? <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.1rem', overflowWrap: 'break-word' }}>{sub}</div> : null}
    </div>
  )
}

function Group({ title, children }) {
  return (
    <div style={{ marginTop: '0.9rem' }}>
      <h3 style={{
        fontSize: 11, fontWeight: 700, color: 'var(--text-muted)',
        textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 8px',
      }}>
        {title}
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {children}
      </div>
    </div>
  )
}

export default function NativeDashboard({ chart, keyedName, keyedPlace, userId }) {
  const facts = useMemo(() => buildNativeDashboard({
    ...chart,
    birth_data: {
      ...(chart?.birth_data || {}),
      name: chart?.birth_data?.name || keyedName || '',
      place_of_birth: chart?.birth_data?.place_of_birth || chart?.place_of_birth || keyedPlace || '',
    },
  }), [chart, keyedName, keyedPlace])

  const savedNaazhigai = chart?.birth_data?.naazhigai
  const savedVinazhigai = chart?.birth_data?.vinazhigai
  const [tamilTime, setTamilTime] = useState(
    savedNaazhigai != null ? { naazhigai: savedNaazhigai, vinazhigai: savedVinazhigai } : null,
  )
  const [triggers, setTriggers] = useState(null)
  const [transitGandantaPoints, setTransitGandantaPoints] = useState([])
  const natalGandantaPoints = useMemo(() => natalGandanta(chart), [chart])

  useEffect(() => {
    if (savedNaazhigai != null) {
      setTamilTime({ naazhigai: savedNaazhigai, vinazhigai: savedVinazhigai })
      return undefined
    }
    if (!chart?.birth_data?.dob) return undefined
    let cancelled = false
    api.post('/tamil-time', chartPayload(chart, userId))
      .then((res) => { if (!cancelled) setTamilTime(res.data) })
      .catch(() => { if (!cancelled) setTamilTime(null) })
    return () => { cancelled = true }
  }, [chart, userId, savedNaazhigai, savedVinazhigai])

  useEffect(() => {
    if (!chart?.birth_data?.dob) return undefined
    let cancelled = false
    api.post('/ashtakavarga/triggers', chartPayload(chart, userId))
      .then((res) => { if (!cancelled) setTriggers(res.data) })
      .catch(() => { if (!cancelled) setTriggers(null) })
    return () => { cancelled = true }
  }, [chart, userId])

  useEffect(() => {
    if (chart?.ascendant?.sign_index == null && !chart?.ascendant?.sign) return undefined
    let cancelled = false
    const location = resolvePanchangamLocation(keyedPlace, chart)
    const tz = chart?.birth_data?.timezone || 'Asia/Kolkata'
    const date = new Date().toLocaleDateString('en-CA', { timeZone: tz })
    api.get('/transit-chart', { params: { date, location } })
      .then((res) => { if (!cancelled) setTransitGandantaPoints(transitGandanta(res.data, chart)) })
      .catch(() => { if (!cancelled) setTransitGandantaPoints([]) })
    return () => { cancelled = true }
  }, [chart, keyedPlace])

  const date = formatBirthDate(facts.date)
  const meta = [date, facts.time, facts.place, facts.weekday].filter(Boolean).join(' · ')
  const traditional = tamilTime?.naazhigai != null
    ? `${tamilTime.naazhigai} naazhigai · ${tamilTime.vinazhigai} vinazhigai`
    : ''
  const traditionalTa = tamilTime?.naazhigai != null
    ? `${tamilTime.naazhigai} நாழிகை · ${tamilTime.vinazhigai} வினாழிகை`
    : ''
  const badhakaValue = facts.badhaka
    ? `${facts.badhaka.planet}${facts.badhaka.star ? ' *' : ''}`
    : ''

  if (!facts.name && !meta && !facts.lagnaLord) return null

  return (
    <section
      className="rounded-xl mb-6"
      style={{
        background: 'var(--card-bg)',
        border: '1px solid var(--card-border)',
        boxShadow: 'var(--card-shadow)',
        padding: '16px 18px',
      }}
      aria-label="Birth details"
    >
      {facts.name && (
        <h2 style={{ margin: 0, fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)' }}>
          {facts.name}
        </h2>
      )}
      {meta && (
        <p style={{ margin: facts.name ? '4px 0 0' : 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          {meta}
        </p>
      )}
      {traditional && (
        <p style={{ margin: '2px 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          {traditional}
          <span style={{ display: 'block', color: 'var(--text-muted)' }}>{traditionalTa}</span>
        </p>
      )}

      <Group title="Birth">
        <Fact label="Tithi" value={facts.tithi} />
        <Fact label="Karanam" value={facts.karana} />
        <Fact label="Yogam" value={facts.yoga} />
        <Fact label="Yogi" value={withStar(facts.yogi, facts.yogiStar)} />
        <Fact label="Avayogi" value={withStar(facts.avayogi, facts.avayogiStar)} />
        <Fact label="Duplicate yogi" value={withStar(facts.duplicateYogi, facts.duplicateStar)} />
        <Fact label="Thithi soonyam" value={facts.soonya} />
      </Group>

      <Group title="Lords">
        <Fact label="Lagna lord" value={facts.lagnaLord?.planet} sub={facts.lagnaLord?.detail} />
        <Fact label="Badhaka lord" value={badhakaValue} sub={facts.badhaka ? `பாதகாதிபதி · ${facts.badhaka.detail}` : ''} wide />
        <Fact
          label="Indu lagna"
          value={facts.indu ? `${facts.indu.sign} · house ${facts.indu.house}` : ''}
          sub={facts.indu ? `Lord ${facts.indu.lord}` : ''}
        />
        <Fact label="Gandanta" value={pointLine(natalGandantaPoints)} sub={pointJunctions(natalGandantaPoints)} />
        {transitGandantaPoints.length > 0 && (
          <Fact
            hot
            label="Transit in gandanta"
            value={pointLine(transitGandantaPoints)}
            sub={pointJunctions(transitGandantaPoints)}
          />
        )}
      </Group>

      {facts.period && (
        <Group title="Now">
          <Fact label="Dasha / bhukti" value={facts.period} />
        </Group>
      )}

      {triggers?.available && (
        <Group title="Triggers">
          {(triggers.hotspots || []).map((hotspot) => (
            <Fact
              key={hotspot.nakshatra}
              wide
              label={hotspot.is_triple_trigger ? 'Triple hotspot' : 'Hotspot'}
              value={formatHotspotValue(hotspot, triggers.all_triggers)}
            />
          ))}
          <div
            className="col-span-2 sm:col-span-3"
            style={{
              background: 'var(--highlight-bg)',
              border: '1px solid var(--card-border)',
              borderRadius: '0.65rem',
              padding: '0.65rem 0.75rem',
            }}
          >
            <div style={{ fontSize: '0.68rem', letterSpacing: '0.04em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
              Trigger nakshatras
            </div>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-y-1 sm:gap-x-3" style={{ margin: '0.35rem 0 0', padding: 0, listStyle: 'none' }}>
              {(triggers.all_triggers || []).map((item) => (
                <li key={item.planet} style={{ fontSize: '0.8rem', color: 'var(--text-primary)' }}>
                  {formatTriggerItem(item)}
                </li>
              ))}
            </ul>
          </div>
        </Group>
      )}

      {facts.badhaka?.star && (
        <p style={{ margin: '10px 0 0', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          * This lord sits in a kendra, a trikona, or its own sign.
        </p>
      )}
    </section>
  )
}
