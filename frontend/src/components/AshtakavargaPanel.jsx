/**
 * AshtakavargaPanel.jsx
 * Displays BAV planet totals + SAV house-wise chart with colour coding.
 */
import { useState, useEffect } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'

const PLANET_LABELS = {
  SUN:'☉ Sun', MOON:'☽ Moon', MARS:'♂ Mars', MERCURY:'☿ Mercury',
  JUPITER:'♃ Jupiter', VENUS:'♀ Venus', SATURN:'♄ Saturn', ASCENDANT:'⬆ Lagna',
}

const SAV_EXPECTED_TOTALS = {
  SUN:48, MOON:49, MARS:39, MERCURY:54, JUPITER:56, VENUS:52, SATURN:39,
}

function colour(pts, isSav = false) {
  if (isSav) {
    if (pts >= 30) return '#27ae60'
    if (pts >= 25) return '#f39c12'
    if (pts >= 20) return '#e67e22'
    return '#e74c3c'
  }
  if (pts >= 5) return '#27ae60'
  if (pts >= 3) return '#f39c12'
  return '#e74c3c'
}

function Bar({ value, max, col }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:6 }}>
      <div style={{
        flex:1, height:8, background:'var(--card-border)', borderRadius:4, overflow:'hidden'
      }}>
        <div style={{
          width:`${Math.round((value/max)*100)}%`, height:'100%',
          background:col, borderRadius:4, transition:'width 0.4s'
        }}/>
      </div>
      <span style={{ fontSize:12, fontWeight:700, color:col, minWidth:20 }}>{value}</span>
    </div>
  )
}

export default function AshtakavargaPanel({ chart, userId }) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')
  const [view,    setView]    = useState('sav')  // 'sav' | planet key

  useEffect(() => {
    if (!chart) return
    setLoading(true)
    api.post('/ashtakavarga', chartPayload(chart, userId))
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Could not load Ashtakavarga.'))
      .finally(() => setLoading(false))
  }, [chart, userId])

  if (loading) return (
    <div style={{ textAlign:'center', padding:'32px 0', color:'var(--orange)', fontSize:13 }}
      className="animate-pulse">
      Calculating Ashtakavarga…
    </div>
  )
  if (error) return (
    <div style={{ color:'var(--error-text)', background:'var(--error-bg)',
      border:`1px solid var(--error-border)`, borderRadius:10, padding:'12px 16px', fontSize:13 }}>
      ⚠️ {error}
    </div>
  )
  if (!data) return null

  const bav   = data.bav   || {}
  const sav   = data.sav   || {}
  const savHW = sav.house_wise || []
  const lagna = data.lagna_sign || ''

  const planets = ['SUN','MOON','MARS','MERCURY','JUPITER','VENUS','SATURN']

  return (
    <div style={{ marginTop:8 }}>
      {/* Section header */}
      <div style={{
        display:'flex', alignItems:'center', justifyContent:'space-between',
        marginBottom:14
      }}>
        <h3 style={{ fontSize:14, fontWeight:700, color:'var(--text-secondary)',
          textTransform:'uppercase', letterSpacing:'0.07em', margin:0 }}>
          ✦ Ashtakavarga
        </h3>
        <span style={{ fontSize:11, color:'var(--text-muted)' }}>
          SAV Total: {sav.total || 0} · Lagna: {lagna} · feeds Gochara scores
        </span>
      </div>

      {/* View tabs */}
      <div style={{ display:'flex', flexWrap:'wrap', gap:6, marginBottom:14 }}>
        {[{key:'sav', label:'Sarva (SAV)'}, ...planets.map(p=>({key:p, label:PLANET_LABELS[p]}))].map(({key,label}) => (
          <button key={key} onClick={() => setView(key)}
            style={{
              padding:'4px 10px', borderRadius:14, cursor:'pointer',
              fontSize:11, fontWeight:600,
              background: view===key ? 'var(--orange)' : 'var(--chip-bg)',
              color: view===key ? 'var(--accent-dark)' : 'var(--text-secondary)',
              border: view===key ? 'none' : '1px solid var(--chip-border)',
            }}>
            {label}
          </button>
        ))}
      </div>

      {/* SAV chart */}
      {view === 'sav' && (
        <div>
          <div className="av-house-grid" style={{ marginBottom:12 }}>
            {savHW.map((pts, i) => {
              const col = colour(pts, true)
              return (
                <div key={i} style={{
                  background:'var(--card-bg)', border:`2px solid ${col}`,
                  borderRadius:10, padding:'8px 10px', textAlign:'center',
                }}>
                  <div style={{ fontSize:10, color:'var(--text-muted)', marginBottom:2 }}>H{i+1}</div>
                  <div style={{ fontSize:20, fontWeight:800, color:col }}>{pts}</div>
                  <div style={{ fontSize:9, color:'var(--text-muted)' }}>
                    {pts>=30?'Strong':pts>=25?'Good':pts>=20?'Avg':'Weak'}
                  </div>
                </div>
              )
            })}
          </div>
          {/* SAV planet totals summary */}
          <div style={{
            background:'var(--card-bg)', border:'1px solid var(--card-border)',
            borderRadius:10, padding:'12px 14px',
          }}>
            <div style={{ fontSize:11, fontWeight:700, color:'var(--text-muted)',
              textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:10 }}>
              Planet Totals (expected in parentheses)
            </div>
            <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
              {planets.map(p => {
                const pData = bav[p] || {}
                const total = pData.total || 0
                const exp   = SAV_EXPECTED_TOTALS[p] || 48
                const col   = colour(total >= exp * 0.9 ? 4 : total >= exp * 0.7 ? 3 : 1)
                return (
                  <div key={p} style={{ display:'grid', gridTemplateColumns:'90px 1fr', alignItems:'center', gap:8 }}>
                    <span style={{ fontSize:12, color:'var(--text-secondary)' }}>
                      {PLANET_LABELS[p]}
                    </span>
                    <Bar value={total} max={exp+5} col={col} />
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Individual BAV chart */}
      {view !== 'sav' && bav[view] && (() => {
        const pData = bav[view]
        const hw    = pData.house_wise || []
        const pinda = pData.shodhya_pinda || {}
        return (
          <div>
            <div className="av-house-grid" style={{ marginBottom:12 }}>
              {hw.map((pts, i) => {
                const col = colour(pts)
                return (
                  <div key={i} style={{
                    background:'var(--card-bg)', border:`2px solid ${col}`,
                    borderRadius:10, padding:'8px', textAlign:'center',
                  }}>
                    <div style={{ fontSize:10, color:'var(--text-muted)', marginBottom:2 }}>H{i+1}</div>
                    <div style={{ fontSize:20, fontWeight:800, color:col }}>{pts}</div>
                  </div>
                )
              })}
            </div>
            {/* Pinda info */}
            {pinda.shodhya_pinda && (
              <div style={{
                background:'var(--card-bg)', border:'1px solid var(--card-border)',
                borderRadius:10, padding:'12px 14px', fontSize:12,
              }}>
                <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(90px, 1fr))', gap:8 }}>
                  {[
                    { label:'Total BAV', value: pData.total },
                    { label:'Shodhya Pinda', value: pinda.shodhya_pinda },
                    { label:'Trigger Nakshatra', value: pinda.trigger_nakshatra },
                  ].map(({label, value}) => (
                    <div key={label} style={{
                      background:'var(--table-header)', borderRadius:8, padding:'8px 10px'
                    }}>
                      <div style={{ fontSize:10, color:'var(--text-muted)', marginBottom:3 }}>{label}</div>
                      <div style={{ fontWeight:700, color:'var(--text-primary)' }}>{value}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )
      })()}
    </div>
  )
}
