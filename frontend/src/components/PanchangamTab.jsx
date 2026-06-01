/**
 * PanchangamTab.jsx
 * =================
 * Unified Panchangam tab — date picker, location selector, 5-limb data,
 * inauspicious kalams, AND a live South Indian transit chart for the selected
 * date with degree + pada + retrograde details.
 *
 * Layout:
 *   Top: date + location controls (full width)
 *   Desktop: [Panchangam data — left] | [Transit chart — right]
 *   Mobile:  Panchangam data stacked, then Transit chart below
 */

import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import SouthIndianChart from './SouthIndianChart'

// ── Constants ────────────────────────────────────────────────────────────────

const LOCATIONS = [
  'Chennai', 'Bangalore', 'Mumbai', 'Delhi',
  'Hyderabad', 'Coimbatore', 'Erlangen',
]

const SPECIAL_TITHIS = {
  Purnima:  { label: '🌕 Purnima',  style: { background: '#FFFBF0', border: '1px solid #FF9900', color: '#E47911' } },
  Amavasya: { label: '🌑 Amavasya', style: { background: '#F5F5F5', border: '1px solid #CCC',    color: '#555' } },
}

const KALAM_CONFIG = [
  { key: 'rahu',    start: 'rahu_kalam_start',   end: 'rahu_kalam_end',   label: 'Rahu Kalam', dotColor: '#D13212', activeColor: '#D13212' },
  { key: 'gulikai', start: 'gulikai_kalam_start', end: 'gulikai_kalam_end',label: 'Gulikai',    dotColor: '#FF9900', activeColor: '#E47911' },
  { key: 'yama',    start: 'yamaganda_start',     end: 'yamaganda_end',    label: 'Yamaganda',  dotColor: '#E47911', activeColor: '#E47911' },
]

// ── Style helpers ────────────────────────────────────────────────────────────

const S = {
  label: { color: '#888' },
  value: { color: '#232F3E' },
  sub:   { color: '#AAA' },
  card:  { background: '#FFFFFF', border: '1px solid #E8DDD0', borderRadius: '12px', boxShadow: '0 2px 6px rgba(0,0,0,0.06)' },
  input: { background: '#FFFFFF', border: '1px solid #C8BAA8', color: '#1A1A1A', borderRadius: '8px' },
}

// ── Utility formatters ────────────────────────────────────────────────────────

function fmtTime(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit', hour12: true, timeZone: 'Asia/Kolkata',
    })
  } catch { return iso }
}

function fmtDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('en-IN', {
      day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
      hour12: true, timeZone: 'Asia/Kolkata',
    })
  } catch { return iso }
}

function isNow(startIso, endIso) {
  if (!startIso || !endIso) return false
  const now = Date.now()
  return now >= new Date(startIso).getTime() && now <= new Date(endIso).getTime()
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SectionLabel({ children }) {
  return (
    <div className="text-xs uppercase tracking-wider mb-1" style={S.label}>{children}</div>
  )
}

function PanchangamLimbs({ data }) {
  const special     = SPECIAL_TITHIS[data.tithi_name]
  const specialNext = !special ? SPECIAL_TITHIS[data.next_tithi_name] : null

  return (
    <div className="space-y-3">
      {/* Sunrise / Sunset */}
      <div className="flex justify-between text-xs px-1" style={S.sub}>
        <span>☀ Sunrise: {fmtTime(data.sunrise)}</span>
        <span>🌇 Sunset: {fmtTime(data.sunset)}</span>
      </div>

      {/* Purnima / Amavasya banner */}
      {special && (
        <div className="rounded-xl px-4 py-2 flex items-center gap-3" style={special.style}>
          <span className="text-sm font-bold">{special.label}</span>
          <span className="text-xs" style={S.sub}>{data.nakshatra_name} nakshatra</span>
        </div>
      )}
      {specialNext && (
        <div className="rounded-xl px-4 py-2 flex items-center justify-between" style={specialNext.style}>
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold">{specialNext.label}</span>
            <span className="text-xs" style={S.sub}>begins after {fmtTime(data.tithi_end_time)}</span>
          </div>
          <span className="text-xs italic" style={{ color: '#AAA' }}>Kshaya Tithi</span>
        </div>
      )}

      {/* 5 limbs grid */}
      <div className="grid grid-cols-2 gap-x-5 gap-y-3 p-4" style={S.card}>

        {/* Vaaram */}
        <div>
          <SectionLabel>Vaaram</SectionLabel>
          <div className="font-semibold text-sm" style={S.value}>{data.vaaram_name}</div>
          <div className="text-xs mt-0.5" style={S.sub}>Lord: {data.vaaram_lord}</div>
        </div>

        {/* Tithi */}
        <div>
          <SectionLabel>Tithi</SectionLabel>
          <div className="font-semibold text-sm" style={S.value}>
            {data.tithi_paksha} {data.tithi_name}
          </div>
          <div className="text-xs mt-0.5" style={S.sub}>
            Ends {fmtDate(data.tithi_end_time)}
            {data.next_tithi_name && ` → ${data.next_tithi_name}`}
          </div>
        </div>

        {/* Nakshatra */}
        <div>
          <SectionLabel>Nakshatra</SectionLabel>
          <div className="font-semibold text-sm" style={S.value}>
            {data.nakshatra_name}{' '}
            <span style={S.sub}>P{data.nakshatra_pada}</span>
          </div>
          <div className="text-xs mt-0.5" style={S.sub}>
            Lord: {data.nakshatra_lord} · Ends {fmtDate(data.nakshatra_end_time)}
          </div>
        </div>

        {/* Yogam */}
        <div>
          <SectionLabel>Yogam</SectionLabel>
          <div className="font-semibold text-sm" style={S.value}>{data.yogam_name}</div>
          {data.next_yogam_name && (
            <div className="text-xs mt-0.5" style={S.sub}>Next: {data.next_yogam_name}</div>
          )}
        </div>

        {/* Karanam */}
        <div>
          <SectionLabel>Karanam</SectionLabel>
          <div className="font-semibold text-sm" style={S.value}>{data.karanam_name}</div>
          <div className="text-xs mt-0.5" style={S.sub}>
            Ends {fmtDate(data.karanam_end_time)}
            {data.next_karanam_name && ` → ${data.next_karanam_name}`}
          </div>
        </div>

      </div>

      {/* Inauspicious timings */}
      <div className="p-4" style={S.card}>
        <SectionLabel>Inauspicious Timings</SectionLabel>
        <div className="space-y-2 mt-1">
          {KALAM_CONFIG.map(({ key, start, end, label, dotColor, activeColor }) => {
            const active = isNow(data[start], data[end])
            return (
              <div key={key} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`w-2 h-2 rounded-full ${active ? 'animate-pulse' : ''}`}
                    style={{ background: dotColor, opacity: active ? 1 : 0.5 }}
                  />
                  <span className="text-sm" style={{
                    color: active ? activeColor : '#888',
                    fontWeight: active ? 700 : 400,
                  }}>
                    {label}
                    {active && <span className="ml-1 text-xs opacity-70">● NOW</span>}
                  </span>
                </div>
                <span className="text-xs tabular-nums" style={S.sub}>
                  {fmtTime(data[start])} – {fmtTime(data[end])}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── Planet details table below the chart ─────────────────────────────────────

function TransitPlanetTable({ planetPositions, ascendant }) {
  const ORDER = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']
  const SYMS  = { Sun:'☉', Moon:'☽', Mars:'♂', Mercury:'☿', Jupiter:'♃', Venus:'♀', Saturn:'♄', Rahu:'☊', Ketu:'☋' }

  return (
    <div className="mt-3 overflow-x-auto">
      <table style={{
        width: '100%', borderCollapse: 'collapse',
        fontFamily: "'Inter', system-ui, sans-serif",
        fontSize: '0.72rem', color: '#1A1A1A',
      }}>
        <thead>
          <tr style={{ background: '#FFF8F0', borderBottom: '2px solid #FF9900' }}>
            <th style={th}>Planet</th>
            <th style={th}>Sign</th>
            <th style={{ ...th, textAlign: 'right' }}>Deg</th>
            <th style={{ ...th, textAlign: 'center' }}>Pada</th>
            <th style={th}>Nakshatra</th>
            <th style={{ ...th, textAlign: 'center' }}>H</th>
            <th style={{ ...th, textAlign: 'center' }}>℞</th>
          </tr>
        </thead>
        <tbody>
          {/* Ascendant row */}
          {ascendant && (
            <tr style={{ background: '#FFF8F0', borderBottom: '1px solid #EEE' }}>
              <td style={td}><span style={{ color: '#FF9900', fontWeight: 700 }}>⬆ ASC</span></td>
              <td style={{ ...td, fontWeight: 700, color: '#232F3E' }}>{ascendant.sign}</td>
              <td style={{ ...td, textAlign: 'right', fontFamily: 'monospace', color: '#555' }}>
                {ascendant.degree_in_sign?.toFixed(2)}°
              </td>
              <td style={{ ...td, textAlign: 'center', color: '#555' }}>{ascendant.pada}</td>
              <td style={{ ...td, color: '#444' }}>{ascendant.nakshatra}</td>
              <td style={{ ...td, textAlign: 'center', color: '#888' }}>—</td>
              <td style={{ ...td, textAlign: 'center', color: '#888' }}>—</td>
            </tr>
          )}
          {ORDER.map(name => {
            const p = planetPositions?.[name]
            if (!p) return null
            return (
              <tr key={name} style={{ borderBottom: '1px solid #EEE' }}>
                <td style={td}>
                  <span style={{ marginRight: 4 }}>{SYMS[name]}</span>
                  <span style={{ fontWeight: 600, color: '#232F3E' }}>{name}</span>
                </td>
                <td style={{ ...td, fontWeight: 600, color: '#232F3E' }}>{p.sign}</td>
                <td style={{ ...td, textAlign: 'right', fontFamily: 'monospace', color: '#555' }}>
                  {p.degree_in_sign?.toFixed(2)}°
                </td>
                <td style={{ ...td, textAlign: 'center', color: '#555' }}>{p.pada}</td>
                <td style={{ ...td, color: '#444' }}>{p.nakshatra}</td>
                <td style={{ ...td, textAlign: 'center', fontWeight: 700, color: '#FF9900' }}>H{p.house}</td>
                <td style={{ ...td, textAlign: 'center', color: p.retrograde ? '#D13212' : '#CCC', fontWeight: 700 }}>
                  {p.retrograde ? '℞' : '—'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

const th = {
  padding: '6px 8px', fontWeight: 700, fontSize: '0.65rem',
  textTransform: 'uppercase', letterSpacing: '0.05em',
  whiteSpace: 'nowrap', textAlign: 'left', color: '#444',
}
const td = { padding: '5px 8px', whiteSpace: 'nowrap' }

// ── Main component ────────────────────────────────────────────────────────────

export default function PanchangamTab() {
  const todayStr = new Date().toISOString().split('T')[0]

  const [date, setDate]           = useState(todayStr)
  const [location, setLocation]   = useState('Chennai')
  const [panch, setPanch]         = useState(null)
  const [transit, setTransit]     = useState(null)
  const [loadingP, setLoadingP]   = useState(false)
  const [loadingT, setLoadingT]   = useState(false)
  const [errorP, setErrorP]       = useState('')
  const [errorT, setErrorT]       = useState('')

  // Fetch both panchangam and transit chart whenever date/location changes
  const fetchAll = useCallback(async () => {
    setLoadingP(true)
    setLoadingT(true)
    setErrorP('')
    setErrorT('')

    // Panchangam
    try {
      const isToday = date === todayStr
      const res = isToday
        ? await api.get('/panchangam/today', { params: { location } })
        : await api.get('/panchangam/date',  { params: { date, location } })
      setPanch(res.data)
    } catch (e) {
      setErrorP(e.response?.data?.detail || 'Could not load Panchangam.')
    } finally {
      setLoadingP(false)
    }

    // Transit chart
    try {
      const res = await api.get('/transit-chart', { params: { date, location } })
      setTransit(res.data)
    } catch (e) {
      setErrorT(e.response?.data?.detail || 'Could not load transit chart.')
    } finally {
      setLoadingT(false)
    }
  }, [date, location, todayStr])

  useEffect(() => { fetchAll() }, [fetchAll])

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">

      {/* ── Controls ── */}
      <div className="flex gap-3 mb-6">
        <input
          type="date" value={date}
          min="2020-01-01" max="2030-12-31"
          onChange={e => setDate(e.target.value)}
          className="flex-1 px-3 py-2.5 text-sm focus:outline-none rounded-xl"
          style={S.input}
        />
        <select
          value={location}
          onChange={e => setLocation(e.target.value)}
          className="flex-1 px-3 py-2.5 text-sm focus:outline-none rounded-xl"
          style={S.input}
        >
          {LOCATIONS.map(l => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
      </div>

      {/* ── Two-column layout: Panchangam left, Transit chart right ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* ── Left: Panchangam data ── */}
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide mb-4" style={S.label}>
            🗓 Panchangam — {date}
          </h2>

          {loadingP && (
            <div className="text-sm py-6 text-center animate-pulse" style={{ color: '#FF9900' }}>
              Loading Panchangam…
            </div>
          )}
          {errorP && (
            <div className="text-sm rounded-xl px-4 py-3 mb-3"
              style={{ color: '#D13212', background: '#FFF5F3', border: '1px solid #FDBDAD' }}>
              {errorP}
            </div>
          )}
          {panch && !loadingP && <PanchangamLimbs data={panch} />}
        </div>

        {/* ── Right: Transit chart ── */}
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide mb-4" style={S.label}>
            🪐 Sky Chart — Planetary Transits · {location} · Noon
          </h2>

          {loadingT && (
            <div className="text-sm py-6 text-center animate-pulse" style={{ color: '#FF9900' }}>
              Computing transit chart…
            </div>
          )}
          {errorT && (
            <div className="text-sm rounded-xl px-4 py-3 mb-3"
              style={{ color: '#D13212', background: '#FFF5F3', border: '1px solid #FDBDAD' }}>
              {errorT}
            </div>
          )}

          {transit && !loadingT && (
            <div>
              <div className="rounded-xl p-3 mb-4"
                style={{ background: '#FFFFFF', border: '1px solid #E8DDD0', boxShadow: '0 2px 6px rgba(0,0,0,0.06)' }}>
                <SouthIndianChart
                  title="Transit"
                  subtitle={`${date} · ${location} · Noon`}
                  planetPositions={transit.planet_positions}
                  lagnaSignIndex={transit.ascendant?.sign_index}
                  showDetails={true}
                />
              </div>

              {/* Planet details table */}
              <div className="rounded-xl overflow-hidden"
                style={{ background: '#FFFFFF', border: '1px solid #E8DDD0', boxShadow: '0 2px 6px rgba(0,0,0,0.06)' }}>
                <div className="px-4 py-2.5" style={{ borderBottom: '1px solid #EEE', background: '#FFF8F0' }}>
                  <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#888' }}>
                    Planet Details
                  </span>
                  <span className="text-xs ml-3" style={{ color: '#AAA' }}>
                    Ayanamsa: Lahiri {transit.ayanamsa_value?.toFixed(4)}°
                  </span>
                </div>
                <div className="px-2 py-2">
                  <TransitPlanetTable
                    planetPositions={transit.planet_positions}
                    ascendant={transit.ascendant}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
