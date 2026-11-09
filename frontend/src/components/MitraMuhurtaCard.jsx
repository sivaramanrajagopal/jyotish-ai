/**
 * Mitra muhurta: Ashwini + Mesha lagna, and Anusham + Vrischika lagna.
 * Default shows this month; the full list and other months open on demand.
 */
import { useMemo, useState } from 'react'
import { useApiResult } from '../hooks/useApiResult'
import api from '../api/client'
import { localISODate } from '../lib/dates'

const S = {
  card: { background: 'var(--card-bg)', border: '1px solid var(--card-border)', borderRadius: '12px', boxShadow: 'var(--card-shadow)' },
  muted: { color: 'var(--text-muted)' },
  primary: { color: 'var(--text-primary)' },
  secondary: { color: 'var(--text-secondary)' },
}

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]
const YEAR_CHOICES = Array.from({ length: 11 }, (_, i) => String(2020 + i))

function currentMonth() {
  return localISODate().slice(0, 7)
}

function monthParts(value) {
  const fallback = currentMonth()
  const [year, month] = String(value || fallback).split('-')
  return { year: year || fallback.slice(0, 4), month: month || fallback.slice(5, 7) }
}

function fmtRange(startIso, endIso, timeZone) {
  const opts = { hour: '2-digit', minute: '2-digit', hour12: true, timeZone }
  try {
    const start = new Date(startIso).toLocaleTimeString('en-IN', opts)
    const end = new Date(endIso).toLocaleTimeString('en-IN', opts)
    return `${start} – ${end}`
  } catch {
    return '—'
  }
}

function fmtDay(iso, timeZone) {
  try {
    return new Date(iso).toLocaleDateString('en-IN', {
      weekday: 'short', day: 'numeric', month: 'short', timeZone,
    })
  } catch {
    return iso
  }
}

function upcomingWindow(windows) {
  const now = Date.now()
  return windows.find((row) => new Date(row.end).getTime() > now) || null
}

export default function MitraMuhurtaCard({
  location = 'Chennai',
  locations = ['Chennai'],
  onSelectDate,
  onSelectLocation,
}) {
  const [month, setMonth] = useState(currentMonth)
  const [open, setOpen] = useState(false)
  const key = location && /^\d{4}-\d{2}$/.test(month) ? `${location}|${month}` : null
  const req = useApiResult(
    key,
    () => api.get('/panchangam/mitra-muhurta', { params: { location, month } }).then((r) => r.data),
  )
  const data = req.error ? null : req.data
  const error = req.error
    ? (typeof req.error?.response?.data?.detail === 'string'
      ? req.error.response.data.detail
      : 'Could not load Mitra muhurta.')
    : ''
  const tz = data?.timezone || 'Asia/Kolkata'
  const next = useMemo(() => (data?.windows ? upcomingWindow(data.windows) : null), [data])
  const grouped = useMemo(() => {
    const days = []
    for (const row of data?.windows || []) {
      const last = days[days.length - 1]
      if (last && last.date === row.date) last.rows.push(row)
      else days.push({ date: row.date, rows: [row] })
    }
    return days
  }, [data])

  return (
    <div className="p-4 mt-4" style={S.card}>
      <div className="text-xs uppercase tracking-wider mb-1" style={S.muted}>Mitra muhurta</div>
      <div className="text-sm font-semibold" style={S.primary}>Loan and debt repayment</div>
      <p className="text-sm mt-1 mb-3" style={{ ...S.secondary, overflowWrap: 'anywhere' }}>
        When Ashwini meets Mesha lagna, or Anusham (Anuradha) meets Vrischika lagna.
        Both signs belong to Mars. Traditional timing, not a promise of repayment.
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-3">
        <label className="panch-controls__field">
          <span className="panch-controls__label">Month</span>
          <select
            value={monthParts(month).month}
            onChange={(event) => setMonth(`${monthParts(month).year}-${event.target.value}`)}
            className="panch-controls__input"
            aria-label="Month"
          >
            {MONTH_NAMES.map((name, index) => {
              const value = String(index + 1).padStart(2, '0')
              return <option key={value} value={value}>{name}</option>
            })}
          </select>
        </label>
        <label className="panch-controls__field">
          <span className="panch-controls__label">Year</span>
          <select
            value={monthParts(month).year}
            onChange={(event) => setMonth(`${event.target.value}-${monthParts(month).month}`)}
            className="panch-controls__input"
            aria-label="Year"
          >
            {YEAR_CHOICES.map((year) => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </label>
        <label className="panch-controls__field col-span-2 sm:col-span-1">
          <span className="panch-controls__label">Location</span>
          <select
            value={location}
            onChange={(event) => onSelectLocation?.(event.target.value)}
            className="panch-controls__input"
            aria-label="Mitra muhurta location"
          >
            {locations.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </label>
      </div>

      {req.loading && (
        <p className="text-sm m-0" style={{ color: 'var(--orange)' }}>Finding this month’s windows…</p>
      )}
      {error && (
        <div>
          <p className="text-sm m-0" style={{ color: 'var(--error-text)' }}>{error}</p>
          <button type="button" onClick={req.reload} className="mt-2 font-semibold min-h-[44px]" style={{ color: 'var(--orange-dark)' }}>
            Try again
          </button>
        </div>
      )}

      {data && !req.loading && (
        <>
          {next ? (
            <button
              type="button"
              className="w-full text-left rounded-lg px-3 py-3 min-h-[44px]"
              style={{ background: 'var(--highlight-bg)', border: '1px solid var(--card-border)' }}
              onClick={() => onSelectDate?.(next.date)}
            >
              <div className="text-xs" style={S.muted}>Next in {month}</div>
              <div className="text-sm font-semibold" style={S.primary}>{fmtDay(next.start, tz)}</div>
              <div className="text-sm" style={S.secondary}>
                {next.label} · {fmtRange(next.start, next.end, tz)}
              </div>
            </button>
          ) : (
            <p className="text-sm m-0" style={S.secondary}>
              {data.count === 0
                ? `No overlapping windows in ${month} at ${location}.`
                : `This month’s ${data.count} windows have already passed.`}
            </p>
          )}

          <button
            type="button"
            className="mt-3 w-full rounded-lg px-3 text-sm font-semibold min-h-[44px]"
            style={{ background: 'var(--surface-muted)', color: 'var(--text-primary)', border: '1px solid var(--card-border)' }}
            aria-expanded={open}
            onClick={() => setOpen((value) => !value)}
          >
            {open ? 'Hide the month list' : `Show all ${data.count} windows`}
          </button>

          {open && (
            <div className="mt-3">
              <ul className="m-0 p-0 list-none">
                {grouped.map((day) => (
                  <li key={day.date} className="py-2" style={{ borderBottom: '1px solid var(--card-border)' }}>
                    <button
                      type="button"
                      className="w-full text-left min-h-[44px]"
                      onClick={() => onSelectDate?.(day.date)}
                    >
                      <div className="text-sm font-semibold" style={S.primary}>{fmtDay(day.rows[0].start, tz)}</div>
                      {day.rows.map((row) => (
                        <div key={`${row.start}-${row.id}`} className="text-sm" style={{ ...S.secondary, overflowWrap: 'anywhere' }}>
                          {row.label} · {fmtRange(row.start, row.end, tz)}
                        </div>
                      ))}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  )
}
