/**
 * Shadbala — ratio bars first, the segmented virupa table behind them.
 * Lives on My Chart. Not a separate tab.
 */
import { useEffect, useState } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'

const GROUP = new Set(['sthana', 'kala', 'total', 'rupas', 'ratio', 'rank'])

const DOMAIN = {
  Sun: 'Self, authority, and vitality',
  Moon: 'Mind, mother, and emotional comfort',
  Mars: 'Effort, courage, and siblings',
  Mercury: 'Speech, skill, and trade',
  Jupiter: 'Wisdom, children, and guidance',
  Venus: 'Comfort, marriage, and the arts',
  Saturn: 'Work, endurance, and delay',
}

function strengthLine(row) {
  const lead = row.rank === 1 ? 'Strongest in this chart. ' : ''
  if (!row.meets_minimum) {
    return `${lead}Short of the strength it needs, so these themes take more support.`
  }
  if (row.ratio >= 1.3) {
    return `${lead}Well above the strength it needs, so these themes can come through readily.`
  }
  if (row.ratio >= 1.1) {
    return `${lead}Above the strength it needs, so these themes can come through.`
  }
  if (row.ratio < 1.05) {
    return `${lead}Meets the strength it needs, with nothing to spare.`
  }
  return `${lead}Just past the strength it needs, so these themes can come through with less margin.`
}

function easeLine(row) {
  if (row.planet === 'Sun' || row.planet === 'Moon') return ''
  if (row.ishta > row.kashta + 2) return ' More ease than strain in how it moves.'
  if (row.kashta > row.ishta + 2) return ' More strain than ease in how it moves.'
  return ' Ease and strain are close.'
}

function chartReading(ranked) {
  const top = ranked[0]?.planet
  const short = ranked.filter((row) => !row.meets_minimum).map((row) => row.planet)
  if (!top) return ''
  if (!short.length) {
    return `${top} is the strongest. Every planet is past the strength it needs to give its results.`
  }
  const list = short.join(' and ')
  const verb = short.length === 1 ? 'is' : 'are'
  return `${top} is the strongest. ${list} ${verb} short of the strength needed to give results fully.`
}

function formatValue(key, value) {
  if (value == null || Number.isNaN(Number(value))) return '—'
  if (key === 'rank') return String(value)
  const n = Number(value)
  if (key === 'minimum' && Number.isInteger(n)) return String(n)
  return n.toFixed(2)
}

export default function ShadbalaCard({ chart, userId }) {
  const embedded = chart?.shadbala?.planets ? chart.shadbala : null
  const [data, setData] = useState(embedded)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (embedded) {
      setData(embedded)
      setError('')
      return undefined
    }
    if (!chart) return undefined
    let cancelled = false
    api.post('/shadbala/analyze', chartPayload(chart, userId))
      .then((res) => { if (!cancelled) setData(res.data) })
      .catch(() => { if (!cancelled) setError('Shadbala could not be calculated.') })
    return () => { cancelled = true }
  }, [chart, userId, embedded])

  if (error) {
    return <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{error}</p>
  }
  if (!data?.planets?.length) return null

  const ranked = [...data.planets].sort((a, b) => a.rank - b.rank)
  const scale = Math.max(1.6, ...ranked.map((row) => row.ratio))
  const byName = Object.fromEntries(data.planets.map((row) => [row.planet, row]))
  const columns = data.table_order || ranked.map((row) => row.planet)

  return (
    <section
      className="rounded-xl mb-6 sm:mb-8"
      style={{
        background: 'var(--card-bg)',
        border: '1px solid var(--card-border)',
        boxShadow: 'var(--card-shadow)',
        padding: '16px 18px',
      }}
      aria-label="Shadbala"
    >
      <h3 style={{
        fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)',
        textTransform: 'uppercase', letterSpacing: '0.07em', margin: '0 0 6px',
      }}>
        Shadbala
      </h3>
      <p style={{ margin: '0 0 8px', fontSize: '0.85rem', lineHeight: 1.45, color: 'var(--text-primary)' }}>
        {chartReading(ranked)}
      </p>
      <p style={{ margin: '0 0 12px', fontSize: '0.75rem', lineHeight: 1.45, color: 'var(--text-muted)' }}>
        The line on each bar is the strength that planet needs. Past the line, it can give its results. Short of the line, those themes need more support. This is capacity, not a promise of events.
        {data.time_note ? ` ${data.time_note}` : ''}
      </p>
      <div style={{ display: 'grid', gap: '0.85rem' }}>
        {ranked.map((row) => (
          <div key={row.planet}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', marginBottom: 4 }}>
              <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.85rem' }}>
                {row.rank}. {row.planet}
              </div>
              <div style={{ fontSize: '0.7rem', color: row.meets_minimum ? 'var(--text-secondary)' : '#c0392b' }}>
                {row.rupas.toFixed(2)} / {formatValue('minimum', row.minimum)}
              </div>
            </div>
            <div style={{ position: 'relative', height: 12, borderRadius: 99, background: 'var(--highlight-bg)' }}>
              <div style={{
                width: `${Math.min(100, (row.ratio / scale) * 100)}%`,
                height: '100%',
                borderRadius: 99,
                background: row.meets_minimum ? 'var(--orange)' : '#c0392b',
              }} />
              <div
                title="Strength required"
                style={{
                  position: 'absolute',
                  left: `${(1 / scale) * 100}%`,
                  top: -2,
                  bottom: -2,
                  width: 2,
                  background: 'var(--text-primary)',
                }}
              />
            </div>
            <p style={{ margin: '4px 0 0', fontSize: '0.78rem', lineHeight: 1.4, color: 'var(--text-secondary)' }}>
              {DOMAIN[row.planet]}. {strengthLine(row)}{easeLine(row)}
            </p>
          </div>
        ))}
      </div>
      <p style={{ margin: '10px 0 0', fontSize: '0.7rem', lineHeight: 1.4, color: 'var(--text-muted)' }}>
        Ease and strain come from exaltation and motion. Sun and Moon already carry that motion inside the day and declination scores, so their ease figure stays at 0.
      </p>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        style={{
          marginTop: '0.75rem',
          background: 'transparent',
          border: '1px solid var(--card-border)',
          borderRadius: '0.4rem',
          padding: '0.3rem 0.6rem',
          fontSize: '0.75rem',
          color: 'var(--text-primary)',
          cursor: 'pointer',
        }}
      >
        {open ? 'Hide Shadbala table' : 'Shadbala table'}
      </button>
      {open && (
        <div style={{ overflowX: 'auto', marginTop: '0.6rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', padding: '6px 8px', borderBottom: '2px solid var(--orange)', color: 'var(--text-secondary)' }}>Bala</th>
                {columns.map((name) => (
                  <th key={name} style={{ textAlign: 'right', padding: '6px 8px', borderBottom: '2px solid var(--orange)', color: 'var(--text-secondary)' }}>{name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(data.rows || []).map((row) => (
                <tr key={row.key} style={{ background: GROUP.has(row.key) ? 'var(--highlight-bg)' : 'transparent' }}>
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid var(--card-border)', fontWeight: GROUP.has(row.key) ? 700 : 500, color: 'var(--text-primary)' }}>
                    {row.label}
                  </td>
                  {columns.map((name) => (
                    <td key={name} style={{ padding: '5px 8px', borderBottom: '1px solid var(--card-border)', textAlign: 'right', color: 'var(--text-secondary)' }}>
                      {formatValue(row.key, byName[name]?.[row.key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
