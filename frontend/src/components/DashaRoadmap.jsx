/**
 * DashaRoadmap.jsx
 * Shows Mahadasha + Bhukti timeline for next 3 years from today.
 */

const PLANET_COLOURS = {
  Sun:     '#E47911', Moon:   '#5B8DD9', Mars:    '#D13212',
  Mercury: '#27ae60', Jupiter:'#8B6914', Venus:   '#C471D4',
  Saturn:  '#667788', Rahu:   '#555555', Ketu:    '#8B4513',
}
const PLANET_ICONS = {
  Sun:'☉', Moon:'☽', Mars:'♂', Mercury:'☿',
  Jupiter:'♃', Venus:'♀', Saturn:'♄', Rahu:'☊', Ketu:'☋',
}

function parseDate(str, isoStr) {
  if (isoStr) {
    const d = new Date(isoStr + 'T12:00:00')
    if (!isNaN(d.getTime())) return d
  }
  if (!str) return null
  const d = new Date(str)
  return isNaN(d.getTime()) ? null : d
}

function monthsBetween(a, b) {
  const msDiff = b - a
  return msDiff / (1000 * 60 * 60 * 24 * 30.44)
}

export default function DashaRoadmap({ chart }) {
  if (!chart) return null

  const dasha = chart.dasha || {}
  const seq   = dasha.antardasha_sequence || []
  const md    = dasha.mahadasha           || {}
  const bh    = dasha.bhukti              || {}

  const today    = new Date()
  const endDate  = new Date(today)
  endDate.setFullYear(endDate.getFullYear() + 3)

  // Filter bhuktis that overlap with the next 3 years
  const visible = seq.filter(b => {
    const start = parseDate(b.start)
    const end   = parseDate(b.end)
    if (!start || !end) return false
    return end >= today && start <= endDate
  })

  if (!visible.length) return null

  // Total window in months
  const windowMonths = monthsBetween(today, endDate)

  return (
    <div style={{ marginTop:8 }}>
      <div style={{
        display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:14
      }}>
        <h3 style={{ fontSize:14, fontWeight:700, color:'var(--text-secondary)',
          textTransform:'uppercase', letterSpacing:'0.07em', margin:0 }}>
          ✦ Dasha Roadmap — Next 3 Years
        </h3>
        <span style={{ fontSize:11, color:'var(--text-muted)' }}>
          {md.planet} Mahadasha
        </span>
      </div>

      {/* Timeline */}
      <div style={{ position:'relative', paddingLeft:16 }}>
        {/* Vertical line */}
        <div style={{
          position:'absolute', left:6, top:0, bottom:0,
          width:2, background:'var(--card-border)',
        }}/>

        {visible.map((b, i) => {
          const start      = parseDate(b.start, b.start_iso)
          const end        = parseDate(b.end, b.end_iso)
          const isCurrent  = b.planet === bh.planet && start <= today && today <= end
          const col        = PLANET_COLOURS[b.planet] || '#888'
          const icon       = PLANET_ICONS[b.planet]  || '●'
          const duration   = monthsBetween(
            start < today ? today : start,
            end   > endDate ? endDate : end
          )
          const widthPct   = Math.max(4, Math.min(100, (duration / windowMonths) * 100))

          // Format dates
          const fmt = (d) => d
            ? `${d.toLocaleString('default',{month:'short'})} ${d.getFullYear()}`
            : ''

          return (
            <div key={i} style={{
              position:'relative', marginBottom:10, paddingLeft:20,
            }}>
              {/* Dot */}
              <div style={{
                position:'absolute', left:-2, top:10,
                width:14, height:14, borderRadius:'50%',
                background: isCurrent ? col : 'var(--card-bg)',
                border:`2px solid ${col}`,
                boxShadow: isCurrent ? `0 0 8px ${col}` : 'none',
                zIndex:1,
              }}/>

              {/* Card */}
              <div style={{
                background:  'var(--card-bg)',
                border:      `1px solid ${isCurrent ? col : 'var(--card-border)'}`,
                borderLeft:  `3px solid ${col}`,
                borderRadius: 10,
                padding:     '10px 12px',
                boxShadow:   isCurrent ? `0 2px 8px ${col}44` : 'none',
              }}>
              <div style={{
                display:'flex', flexWrap:'wrap', justifyContent:'space-between',
                alignItems:'flex-start', gap:8,
              }}>
                <div style={{ flex:'1 1 140px', minWidth:0 }}>
                  <span style={{ fontSize:14, fontWeight:800, color:col }}>
                    {icon} {b.planet}
                  </span>
                  <span style={{ fontSize:11, color:'var(--text-muted)', marginLeft:6 }}>
                    Bhukti in {md.planet} Maha
                  </span>
                  {isCurrent && (
                    <span style={{
                      marginLeft:8, fontSize:9, fontWeight:700, color:'#FFF',
                      background:col, borderRadius:8, padding:'2px 6px',
                    }}>NOW</span>
                  )}
                </div>
                <span style={{ fontSize:11, color:'var(--text-muted)', textAlign:'right', flexShrink:0 }}>
                  {fmt(start)} – {fmt(end)}
                </span>
              </div>

                {/* Progress bar */}
                <div style={{ marginTop:8 }}>
                  <div style={{
                    height:4, background:'var(--card-border)', borderRadius:2, overflow:'hidden'
                  }}>
                    <div style={{
                      width:`${widthPct}%`, height:'100%',
                      background:col, borderRadius:2,
                    }}/>
                  </div>
                  <div style={{ fontSize:10, color:'var(--text-muted)', marginTop:3 }}>
                    {Math.round(duration)} months in this window
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
