/**
 * PersonalPanchangamCard.jsx
 * Personalised daily status: Tara Balam, Chandra Ashtama, Chandrabalam.
 */

import { useState, useEffect } from 'react'
import api from '../api/client'

const TARA_STYLES = {
  green:  { background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.3)',  textColor: '#34d399', dotColor: '#34d399' },
  red:    { background: 'rgba(239,68,68,0.12)',   border: '1px solid rgba(239,68,68,0.3)',   textColor: '#f87171', dotColor: '#f87171' },
  yellow: { background: 'rgba(251,191,36,0.1)',   border: '1px solid rgba(251,191,36,0.3)',  textColor: '#fbbf24', dotColor: '#fbbf24' },
}

function fmt(isoStr) {
  if (!isoStr) return null
  try {
    return new Date(isoStr).toLocaleString('en-IN', {
      day: 'numeric', month: 'short',
      hour: '2-digit', minute: '2-digit',
      hour12: true, timeZone: 'Asia/Kolkata',
    })
  } catch {
    return isoStr
  }
}

export default function PersonalPanchangamCard({ chart }) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const nakIdx  = chart?.moon_nakshatra_index
  const rasiIdx = chart?.moon_rasi_index

  useEffect(() => {
    if (nakIdx == null || rasiIdx == null) return
    setLoading(true)
    api.get('/personal-panchangam/anonymous', {
      params: { natal_nak_index: nakIdx, natal_rasi_index: rasiIdx, timezone: 'Asia/Kolkata' }
    })
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Could not load personal Panchangam.'))
      .finally(() => setLoading(false))
  }, [nakIdx, rasiIdx])

  if (nakIdx == null) return null

  const tara    = data?.tara
  const cb      = data?.chandrabalam
  const ashtama = data?.chandra_ashtama
  const ts      = TARA_STYLES[tara?.colour] || TARA_STYLES.yellow

  const cardStyle = {
    background: 'var(--card-bg)',
    border: '1px solid var(--card-border)',
    borderRadius: '12px',
  }

  return (
    <div className="mb-6 sm:mb-8">
      <h3 className="text-sm font-semibold uppercase tracking-wide px-1 mb-3" style={{ color: 'var(--text-secondary)' }}>
        🌙 Personal Planetary Status — Today
      </h3>

      {loading && (
        <div className="text-center text-sm py-6 animate-pulse" style={{ color: 'var(--orange)' }}>
          Computing your personal Panchangam…
        </div>
      )}

      {error && (
        <div className="text-sm rounded-xl px-4 py-3"
          style={{ color: 'var(--error-text)', background: 'var(--error-bg)', border: '1px solid var(--error-border)' }}>
          {error}
        </div>
      )}

      {data && (
        <div className="space-y-3">

          {ashtama?.is_active ? (
            <div className="rounded-xl px-4 sm:px-5 py-4"
              style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)' }}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">🛡️</span>
                <span className="font-bold text-sm uppercase tracking-wide" style={{ color: '#f87171' }}>
                  Chandra Ashtama Active
                </span>
              </div>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                Moon transiting your 8th sign ({ashtama.ashtama_rasi_name}).
                Avoid new beginnings, major decisions, and important travels.
              </p>
              {ashtama.end && (
                <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
                  Ends: {fmt(ashtama.end)}
                </p>
              )}
              {ashtama.next_ashtama_start && (
                <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                  Next occurrence: {fmt(ashtama.next_ashtama_start)}
                </p>
              )}
            </div>
          ) : (
            <div className="rounded-xl px-4 sm:px-5 py-3 flex flex-wrap items-center justify-between gap-2" style={cardStyle}>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full" style={{ background: '#34d399' }} />
                <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Chandra Ashtama</span>
                <span className="text-sm font-semibold" style={{ color: '#34d399' }}>Not active</span>
              </div>
              {ashtama?.next_ashtama_start && (
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Next: {fmt(ashtama.next_ashtama_start)}</span>
              )}
            </div>
          )}

          {tara && (
            <div className="rounded-xl px-4 sm:px-5 py-4" style={{ background: ts.background, border: ts.border }}>
              <div className="flex items-center justify-between mb-1 flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: ts.dotColor }} />
                  <span className="text-xs uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Tara Balam</span>
                </div>
                <span className="text-xs font-semibold uppercase" style={{ color: ts.textColor }}>
                  {tara.nature}
                </span>
              </div>
              <div className="flex items-baseline gap-2 flex-wrap">
                <span className="text-lg font-bold" style={{ color: ts.textColor }}>{tara.name}</span>
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Tara {tara.position}</span>
              </div>
              <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>{tara.meaning}</p>
              <p className="text-xs mt-1.5" style={{ color: 'var(--text-muted)' }}>
                Natal nak: {data.natal_nak_name} · Today: {data.today_moon_nak} ({data.today_moon_rasi})
              </p>
            </div>
          )}

          {cb && (
            <div className="rounded-xl px-4 sm:px-5 py-3 flex flex-wrap items-center justify-between gap-2" style={
              cb.good
                ? { background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)' }
                : cardStyle
            }>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full" style={{ background: cb.good ? '#34d399' : 'var(--text-muted)' }} />
                <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Chandrabalam</span>
                <span className="text-sm font-semibold" style={{ color: cb.good ? '#34d399' : 'var(--text-muted)' }}>
                  {cb.good ? 'Favourable' : 'Weak'}
                </span>
              </div>
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                Moon in house {cb.house_from_natal} from natal Moon
              </span>
            </div>
          )}

        </div>
      )}
    </div>
  )
}
