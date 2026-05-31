/**
 * DailyPanchangamCard.jsx
 * =======================
 * Standalone always-visible Panchangam panel — cosmic golden theme.
 */

import { useState, useEffect } from 'react'
import api from '../api/client'

const LOCATIONS = [
  'Chennai', 'Bangalore', 'Mumbai', 'Delhi',
  'Hyderabad', 'Coimbatore', 'Erlangen',
]

const SPECIAL_TITHIS = {
  'Purnima':  { label: '🌕 Purnima',  style: { background: 'rgba(251,191,36,0.18)', border: '1px solid rgba(251,191,36,0.45)', color: '#fcd34d' } },
  'Amavasya': { label: '🌑 Amavasya', style: { background: 'rgba(30,20,0,0.7)',     border: '1px solid rgba(251,191,36,0.2)',  color: '#d97706' } },
}

const KALAM_CONFIG = [
  { key: 'rahu',    start: 'rahu_kalam_start',   end: 'rahu_kalam_end',   label: 'Rahu Kalam', dotColor: '#ef4444', textColor: '#fca5a5' },
  { key: 'gulikai', start: 'gulikai_kalam_start', end: 'gulikai_kalam_end',label: 'Gulikai',    dotColor: '#f59e0b', textColor: '#fcd34d' },
  { key: 'yama',    start: 'yamaganda_start',     end: 'yamaganda_end',    label: 'Yamaganda',  dotColor: '#f97316', textColor: '#fdba74' },
]

function fmtTime(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit', hour12: true,
      timeZone: 'Asia/Kolkata',
    })
  } catch { return iso }
}

function fmtDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('en-IN', {
      day: 'numeric', month: 'short',
      hour: '2-digit', minute: '2-digit', hour12: true,
      timeZone: 'Asia/Kolkata',
    })
  } catch { return iso }
}

function isKalamNow(startIso, endIso) {
  if (!startIso || !endIso) return false
  const now = Date.now()
  return now >= new Date(startIso).getTime() && now <= new Date(endIso).getTime()
}

const cardStyle  = { background: 'rgba(251,191,36,0.05)', border: '1px solid rgba(251,191,36,0.18)', borderRadius: '12px' }
const inputStyle = { background: 'rgba(251,191,36,0.07)', border: '1px solid rgba(251,191,36,0.2)', color: '#fef3c7', borderRadius: '8px' }
const labelColor = { color: 'rgba(251,191,36,0.5)' }
const valueColor = { color: '#fef3c7' }
const subColor   = { color: 'rgba(254,243,199,0.35)' }

export default function DailyPanchangamCard() {
  const today = new Date().toISOString().split('T')[0]

  const [location, setLocation] = useState('Chennai')
  const [date, setDate]         = useState(today)
  const [data, setData]         = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')

  useEffect(() => { fetchPanchangam() }, [date, location])

  async function fetchPanchangam() {
    setLoading(true)
    setError('')
    try {
      const isToday = date === today
      const res = isToday
        ? await api.get('/panchangam/today', { params: { location } })
        : await api.get('/panchangam/date',  { params: { date, location } })
      setData(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Could not load Panchangam.')
    } finally {
      setLoading(false)
    }
  }

  const special     = data ? SPECIAL_TITHIS[data.tithi_name] : null
  const specialNext = (data && !special) ? SPECIAL_TITHIS[data.next_tithi_name] : null

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-10">

      {/* Header */}
      <div className="flex items-center justify-between mb-4 px-1">
        <h2 className="text-sm font-semibold uppercase tracking-wide" style={labelColor}>
          🗓 Daily Panchangam
        </h2>
        {data && (
          <span className="text-xs" style={subColor}>
            ☀ {fmtTime(data.sunrise)} &nbsp;·&nbsp; 🌇 {fmtTime(data.sunset)}
          </span>
        )}
      </div>

      {/* Controls */}
      <div className="flex gap-3 mb-4">
        <input
          type="date"
          value={date}
          min="2026-01-01"
          max="2027-12-31"
          onChange={e => setDate(e.target.value)}
          className="flex-1 px-3 py-2 text-sm focus:outline-none"
          style={inputStyle}
        />
        <select
          value={location}
          onChange={e => setLocation(e.target.value)}
          className="flex-1 px-3 py-2 text-sm focus:outline-none"
          style={inputStyle}
        >
          {LOCATIONS.map(l => <option key={l} value={l} style={{ background: '#1a0e00' }}>{l}</option>)}
        </select>
      </div>

      {loading && (
        <div className="text-center text-sm py-8 animate-pulse" style={{ color: 'rgba(251,191,36,0.3)' }}>
          Loading Panchangam…
        </div>
      )}

      {error && (
        <div className="text-sm rounded-xl px-4 py-3" style={{ color: '#fca5a5', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)' }}>
          {error}
        </div>
      )}

      {data && !loading && (
        <div className="space-y-3">

          {special && (
            <div className="rounded-xl px-5 py-3 flex items-center gap-3" style={special.style}>
              <span className="text-base font-bold" style={{ color: special.style.color }}>{special.label}</span>
              <span className="text-xs" style={subColor}>{data.nakshatra_name} nakshatra</span>
            </div>
          )}

          {specialNext && (
            <div className="rounded-xl px-5 py-3 flex items-center justify-between" style={specialNext.style}>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold" style={{ color: specialNext.style.color }}>{specialNext.label}</span>
                <span className="text-xs" style={subColor}>begins today after {fmtTime(data.tithi_end_time)}</span>
              </div>
              <span className="text-xs italic" style={{ color: 'rgba(251,191,36,0.3)' }}>Kshaya Tithi</span>
            </div>
          )}

          {/* 5-limb grid */}
          <div className="p-4 grid grid-cols-2 md:grid-cols-3 gap-4" style={cardStyle}>
            <div>
              <div className="text-xs uppercase tracking-wider mb-1" style={labelColor}>Vaaram</div>
              <div className="font-semibold text-sm" style={valueColor}>{data.vaaram_name}</div>
              <div className="text-xs mt-0.5" style={subColor}>Lord: {data.vaaram_lord}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wider mb-1" style={labelColor}>Tithi</div>
              <div className="font-semibold text-sm" style={valueColor}>{data.tithi_paksha} {data.tithi_name}</div>
              <div className="text-xs mt-0.5" style={subColor}>
                Ends {fmtDate(data.tithi_end_time)}{data.next_tithi_name && ` → ${data.next_tithi_name}`}
              </div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wider mb-1" style={labelColor}>Nakshatra</div>
              <div className="font-semibold text-sm" style={valueColor}>
                {data.nakshatra_name} <span style={subColor}>P{data.nakshatra_pada}</span>
              </div>
              <div className="text-xs mt-0.5" style={subColor}>
                Lord: {data.nakshatra_lord} · Ends {fmtDate(data.nakshatra_end_time)}
              </div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wider mb-1" style={labelColor}>Yogam</div>
              <div className="font-semibold text-sm" style={valueColor}>{data.yogam_name}</div>
              {data.next_yogam_name && <div className="text-xs mt-0.5" style={subColor}>Next: {data.next_yogam_name}</div>}
            </div>
            <div>
              <div className="text-xs uppercase tracking-wider mb-1" style={labelColor}>Karanam</div>
              <div className="font-semibold text-sm" style={valueColor}>{data.karanam_name}</div>
              <div className="text-xs mt-0.5" style={subColor}>
                Ends {fmtDate(data.karanam_end_time)}{data.next_karanam_name && ` → ${data.next_karanam_name}`}
              </div>
            </div>
          </div>

          {/* Kalam timings */}
          <div className="p-4" style={cardStyle}>
            <div className="text-xs uppercase tracking-wider mb-3" style={labelColor}>Inauspicious Timings</div>
            <div className="space-y-2">
              {KALAM_CONFIG.map(({ key, start, end, label, dotColor, textColor }) => {
                const active = isKalamNow(data[start], data[end])
                return (
                  <div key={key} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full ${active ? 'animate-pulse' : ''}`}
                        style={{ background: dotColor, opacity: active ? 1 : 0.5 }}
                      />
                      <span className="text-sm" style={{ color: active ? textColor : 'rgba(254,243,199,0.5)', fontWeight: active ? 600 : 400 }}>
                        {label}{active && <span className="ml-2 text-xs font-normal opacity-70">● NOW</span>}
                      </span>
                    </div>
                    <span className="text-xs tabular-nums" style={subColor}>
                      {fmtTime(data[start])} – {fmtTime(data[end])}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

        </div>
      )}
    </div>
  )
}
