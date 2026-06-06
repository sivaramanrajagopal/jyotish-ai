/**
 * DashaSummaryCard — current Mahadasha + Bhukti at a glance
 */

const PLANET_ICONS = {
  Sun: '☉', Moon: '☽', Mars: '♂', Mercury: '☿',
  Jupiter: '♃', Venus: '♀', Saturn: '♄', Rahu: '☊', Ketu: '☋',
}

const RELATION_COLOUR = {
  Friend: '#27ae60', Enemy: '#e74c3c', Neutral: '#f39c12', Same: '#5B8DD9',
}

export default function DashaSummaryCard({ chart }) {
  const dasha = chart?.dasha
  if (!dasha?.mahadasha?.planet) return null

  const md   = dasha.mahadasha
  const bh   = dasha.bhukti || {}
  const rel  = dasha.relationship
  const relCol = RELATION_COLOUR[rel] || 'var(--text-muted)'

  return (
    <div
      className="rounded-xl mb-6 sm:mb-8"
      style={{
        background: 'var(--card-bg)',
        border: '2px solid var(--highlight-border)',
        boxShadow: 'var(--card-shadow)',
        padding: '16px 18px',
      }}
    >
      <h3 style={{
        fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)',
        textTransform: 'uppercase', letterSpacing: '0.07em', margin: '0 0 12px',
      }}>
        ✦ Current Vimshottari Dasha
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Mahadasha */}
        <div style={{
          background: 'var(--highlight-bg)', borderRadius: 10,
          padding: '12px 14px', border: '1px solid var(--card-border)',
        }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
            Mahadasha
          </div>
          <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--orange)' }}>
            {PLANET_ICONS[md.planet] || '●'} {md.planet}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
            {md.start} – {md.end}
          </div>
          {md.focus && (
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, lineHeight: 1.4 }}>
              {md.focus}
            </div>
          )}
          {md.remaining_years != null && (
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              {md.remaining_years} years remaining
            </div>
          )}
        </div>

        {/* Bhukti */}
        <div style={{
          background: 'var(--highlight-bg)', borderRadius: 10,
          padding: '12px 14px', border: '1px solid var(--card-border)',
        }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
            Bhukti (Antardasha)
          </div>
          <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)' }}>
            {PLANET_ICONS[bh.planet] || '●'} {bh.planet || '—'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
            {bh.start && bh.end ? `${bh.start} – ${bh.end}` : '—'}
          </div>
          {bh.trigger && (
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, lineHeight: 1.4 }}>
              {bh.trigger}
            </div>
          )}
          {bh.remaining_months != null && (
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              {bh.remaining_months} months remaining
            </div>
          )}
        </div>
      </div>

      {rel && (
        <div style={{
          marginTop: 10, fontSize: 12, color: 'var(--text-secondary)',
          padding: '8px 10px', background: 'var(--surface-muted)', borderRadius: 8,
        }}>
          MD–Bhukti relationship:{' '}
          <span style={{ fontWeight: 700, color: relCol }}>{rel}</span>
        </div>
      )}

      {dasha.nakshatra && (
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
          Birth nakshatra: {dasha.nakshatra} · Pada {dasha.pada}
        </div>
      )}
    </div>
  )
}
