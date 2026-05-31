/**
 * PersonalPanchangamCard.jsx
 * Step 6 — Shows personalised daily status:
 *   - Natal Moon nakshatra (static)
 *   - Tara Balam (today's nakshatra vs natal)
 *   - Chandra Ashtama status (red banner if active)
 *   - Chandrabalam indicator
 *
 * Uses GET /personal-panchangam/anonymous with indices from the natal chart.
 * No login required.
 */

import { useState, useEffect } from 'react'
import api from '../api/client'

const TARA_STYLES = {
  green:  { background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.3)',  textColor: '#6ee7b7', dotColor: '#34d399' },
  red:    { background: 'rgba(239,68,68,0.12)',   border: '1px solid rgba(239,68,68,0.3)',   textColor: '#fca5a5', dotColor: '#f87171' },
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

  const subColor  = { color: 'rgba(254,243,199,0.35)' }
  const cardStyle = { background: 'rgba(251,191,36,0.05)', border: '1px solid rgba(251,191,36,0.18)', borderRadius: '12px' }

  return (
    <div className="mb-8">
      <h3 className="text-sm font-semibold uppercase tracking-wide px-1 mb-3" style={{ color: 'rgba(251,191,36,0.5)' }}>
        🌙 Personal Planetary Status — Today
      </h3>

      {loading && (
        <div className="text-center text-sm py-6 animate-pulse" style={{ color: 'rgba(251,191,36,0.3)' }}>
          Computing your personal Panchangam…
        </div>
      )}

      {error && (
        <div className="text-sm rounded-xl px-4 py-3" style={{ color: '#fca5a5', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)' }}>
          {error}
        </div>
      )}

      {data && (
        <div className="space-y-3">

          {/* Chandra Ashtama */}
          {ashtama?.is_active ? (
            <div className="rounded-xl px-5 py-4" style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)' }}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">🛡️</span>
                <span className="font-bold text-sm uppercase tracking-wide" style={{ color: '#fca5a5' }}>
                  Chandra Ashtama Active
                </span>
              </div>
              <p className="text-sm" style={{ color: 'rgba(252,165,165,0.7)' }}>
                Moon transiting your 8th sign ({ashtama.ashtama_rasi_name}).
                Avoid new beginnings, major decisions, and important travels.
              </p>
              {ashtama.end && (
                <p className="text-xs mt-2" style={{ color: 'rgba(252,165,165,0.5)' }}>
                  Ends: {fmt(ashtama.end)}
                </p>
              )}
              {ashtama.next_ashtama_start && (
                <p className="text-xs mt-0.5" style={{ color: 'rgba(252,165,165,0.35)' }}>
                  Next occurrence: {fmt(ashtama.next_ashtama_start)}
                </p>
              )}
            </div>
          ) : (
            <div className="rounded-xl px-5 py-3 flex items-center justify-between" style={cardStyle}>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full" style={{ background: '#34d399' }} />
                <span className="text-sm" style={{ color: 'rgba(254,243,199,0.6)' }}>Chandra Ashtama</span>
                <span className="text-sm font-semibold" style={{ color: '#34d399' }}>Not active</span>
              </div>
              {ashtama?.next_ashtama_start && (
                <span className="text-xs" style={subColor}>Next: {fmt(ashtama.next_ashtama_start)}</span>
              )}
            </div>
          )}

          {/* Tara Balam */}
          {tara && (
            <div className="rounded-xl px-5 py-4" style={{ background: ts.background, border: ts.border }}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: ts.dotColor }} />
                  <span className="text-xs uppercase tracking-wider" style={{ color: 'rgba(254,243,199,0.5)' }}>Tara Balam</span>
                </div>
                <span className="text-xs font-semibold uppercase" style={{ color: ts.textColor }}>
                  {tara.nature}
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-bold" style={{ color: ts.textColor }}>{tara.name}</span>
                <span className="text-xs" style={subColor}>Tara {tara.position}</span>
              </div>
              <p className="text-xs mt-1" style={{ color: 'rgba(254,243,199,0.45)' }}>{tara.meaning}</p>
              <p className="text-xs mt-1.5" style={subColor}>
                Natal nak: {data.natal_nak_name} · Today: {data.today_moon_nak} ({data.today_moon_rasi})
              </p>
            </div>
          )}

          {/* Chandrabalam */}
          {cb && (
            <div className="rounded-xl px-5 py-3 flex items-center justify-between" style={
              cb.good
                ? { background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)' }
                : cardStyle
            }>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full" style={{ background: cb.good ? '#34d399' : '#6b7280' }} />
                <span className="text-sm" style={{ color: 'rgba(254,243,199,0.6)' }}>Chandrabalam</span>
                <span className="text-sm font-semibold" style={{ color: cb.good ? '#34d399' : '#9ca3af' }}>
                  {cb.good ? 'Favourable' : 'Weak'}
                </span>
              </div>
              <span className="text-xs" style={subColor}>
                Moon in house {cb.house_from_natal} from natal Moon
              </span>
            </div>
          )}

        </div>
      )}
    </div>
  )
}
