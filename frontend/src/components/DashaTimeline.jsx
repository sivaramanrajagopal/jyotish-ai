/**
 * DashaTimeline.jsx
 * Full Vimshottari timeline from birth: nine Mahadashas, each opening to its Bhuktis.
 * Data comes from chart.dasha.timeline (ISO dates, Lahiri Moon).
 */
import { useState } from 'react'

const PLANET_COLOURS = {
  Sun: '#E47911', Moon: '#5B8DD9', Mars: '#D13212',
  Mercury: '#27ae60', Jupiter: '#8B6914', Venus: '#C471D4',
  Saturn: '#667788', Rahu: '#555555', Ketu: '#8B4513',
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function fmtDay(iso) {
  const [y, m, d] = String(iso || '').split('-').map(Number)
  if (!y || !m || !d) return ''
  return `${d} ${MONTHS[m - 1]} ${y}`
}

function fmtMonth(iso) {
  const [y, m] = String(iso || '').split('-').map(Number)
  if (!y || !m) return ''
  return `${MONTHS[m - 1]} ${y}`
}

function fmtYears(years) {
  const n = Number(years)
  if (!Number.isFinite(n)) return ''
  return Number.isInteger(n) ? `${n} yrs` : `${n.toFixed(1)} yrs`
}

function Dot({ colour }) {
  return (
    <span
      aria-hidden="true"
      className="inline-block flex-shrink-0 rounded-full mr-2"
      style={{ width: 10, height: 10, background: colour }}
    />
  )
}

function NowBadge({ colour }) {
  return (
    <span
      className="ml-2 rounded-lg px-1.5 py-0.5 text-[10px] font-bold text-white"
      style={{ background: colour }}
    >
      NOW
    </span>
  )
}

function BhuktiList({ maha, today }) {
  return (
    <ol className="list-none m-0 p-0 mt-2 space-y-1">
      {maha.bhuktis.map((b) => {
        const colour = PLANET_COLOURS[b.planet] || '#888'
        const past = b.end <= today
        return (
          <li
            key={`${maha.planet}-${b.planet}-${b.start}`}
            className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-0.5 sm:gap-3 rounded-md px-2.5 py-1.5"
            style={{
              background: b.current ? 'var(--highlight-bg)' : 'transparent',
              border: `1px solid ${b.current ? colour : 'var(--card-border)'}`,
            }}
          >
            <span
              className="flex items-center text-sm font-semibold"
              style={{ color: past && !b.current ? 'var(--text-muted)' : 'var(--text-primary)' }}
            >
              <Dot colour={colour} />
              {maha.planet}–{b.planet}
              {b.current && <NowBadge colour={colour} />}
            </span>
            <span className="text-xs pl-[18px] sm:pl-0" style={{ color: 'var(--text-muted)' }}>
              {fmtDay(b.start)} – {fmtDay(b.end)}
            </span>
          </li>
        )
      })}
    </ol>
  )
}

export default function DashaTimeline({ chart }) {
  const timeline = chart?.dasha?.timeline || []
  const current = timeline.find((row) => row.current)
  const [open, setOpen] = useState(() => (current ? [current.planet] : []))

  if (!timeline.length) return null

  const today = new Date().toISOString().slice(0, 10)
  const first = timeline[0]
  const toggle = (planet) => setOpen((ids) => (
    ids.includes(planet) ? ids.filter((id) => id !== planet) : [...ids, planet]
  ))

  return (
    <div>
      <div className="mb-3">
        <h3
          className="text-sm font-bold uppercase tracking-wide m-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Vimshottari Dasha — full timeline
        </h3>
        <p className="text-xs mt-1 mb-0" style={{ color: 'var(--text-muted)' }}>
          From birth, Lahiri Moon. Born in {first.planet} with {fmtYears(first.years)} left.
          Tap a Mahadasha to see its Bhuktis.
        </p>
      </div>

      <ol className="list-none m-0 p-0 space-y-2">
        {timeline.map((maha) => {
          const colour = PLANET_COLOURS[maha.planet] || '#888'
          const isOpen = open.includes(maha.planet)
          const past = maha.end <= today
          const panelId = `dasha-${maha.planet}-${maha.start}`
          return (
            <li
              key={panelId}
              className="rounded-lg"
              style={{
                background: 'var(--card-bg)',
                border: `1px solid ${maha.current ? colour : 'var(--card-border)'}`,
                borderLeft: `4px solid ${colour}`,
              }}
            >
              <button
                type="button"
                className="w-full text-left px-3 py-2.5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-3 bg-transparent border-0 cursor-pointer"
                style={{ minHeight: 44, color: 'var(--text-primary)' }}
                aria-expanded={isOpen}
                aria-controls={panelId}
                onClick={() => toggle(maha.planet)}
              >
                <span className="flex items-center min-w-0">
                  <span aria-hidden="true" className="mr-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                    {isOpen ? '▾' : '▸'}
                  </span>
                  <Dot colour={colour} />
                  <span
                    className="text-base font-bold"
                    style={{ color: past ? 'var(--text-secondary)' : 'var(--text-primary)' }}
                  >
                    {maha.planet}
                  </span>
                  <span className="ml-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                    {fmtYears(maha.years)}{maha.balance ? ' (balance)' : ''}
                  </span>
                  {maha.current && <NowBadge colour={colour} />}
                </span>
                <span className="text-xs pl-[38px] sm:pl-0" style={{ color: 'var(--text-muted)' }}>
                  {fmtMonth(maha.start)} – {fmtMonth(maha.end)} · age {Math.floor(maha.age_start)}–{Math.floor(maha.age_end)}
                </span>
              </button>
              {isOpen && (
                <div id={panelId} className="px-3 pb-3">
                  <BhuktiList maha={maha} today={today} />
                </div>
              )}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
