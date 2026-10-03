/**
 * Combined period reading — Avastha, Shadbala, BAV, and SAV for the current dasha.
 * Lives on My Chart under the dasha summary. Not a separate tab.
 */
import { useEffect, useState } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'

function LordBlock({ lord }) {
  return (
    <div style={{
      background: 'var(--highlight-bg)',
      borderRadius: 10,
      padding: '12px 14px',
      border: '1px solid var(--card-border)',
    }}>
      <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
        {lord.role}
      </div>
      <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--text-primary)' }}>
        {lord.planet}
      </div>
      {lord.domain && (
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>{lord.domain}</div>
      )}
      {lord.strength && (
        <p style={{ margin: '8px 0 0', fontSize: 13, lineHeight: 1.45, color: 'var(--text-primary)' }}>
          <strong>Strength. </strong>{lord.strength}
        </p>
      )}
      {lord.condition && (
        <p style={{ margin: '6px 0 0', fontSize: 13, lineHeight: 1.45, color: 'var(--text-primary)' }}>
          <strong>Condition. </strong>{lord.condition}
        </p>
      )}
      {lord.ground && (
        <p style={{ margin: '6px 0 0', fontSize: 13, lineHeight: 1.45, color: 'var(--text-primary)' }}>
          <strong>Ground. </strong>{lord.ground}
        </p>
      )}
    </div>
  )
}

export default function PeriodReadingCard({ chart, userId }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!chart?.dasha?.mahadasha?.planet) return undefined
    let cancelled = false
    setError('')
    api.post('/period-reading', chartPayload(chart, userId))
      .then((res) => { if (!cancelled) setData(res.data) })
      .catch(() => { if (!cancelled) setError('The period reading could not be calculated.') })
    return () => { cancelled = true }
  }, [chart, userId])

  if (!chart?.dasha?.mahadasha?.planet) return null
  if (error) {
    return <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: 16 }}>{error}</p>
  }
  if (!data?.lords?.length) return null

  return (
    <section
      className="rounded-xl mb-6 sm:mb-8"
      style={{
        background: 'var(--card-bg)',
        border: '1px solid var(--card-border)',
        boxShadow: 'var(--card-shadow)',
        padding: '16px 18px',
      }}
      aria-label="This period"
    >
      <h3 style={{
        fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)',
        textTransform: 'uppercase', letterSpacing: '0.07em', margin: '0 0 6px',
      }}>
        This period
      </h3>
      <p style={{ margin: '0 0 8px', fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
        {data.period_label}
      </p>
      {data.lead && (
        <p style={{ margin: '0 0 12px', fontSize: '0.85rem', lineHeight: 1.45, color: 'var(--text-primary)' }}>
          {data.lead}
        </p>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {data.lords.map((lord) => (
          <LordBlock key={lord.role} lord={lord} />
        ))}
      </div>
      {data.note && (
        <p style={{ margin: '12px 0 0', fontSize: '0.75rem', lineHeight: 1.45, color: 'var(--text-muted)' }}>
          {data.note}
        </p>
      )}
    </section>
  )
}
