/**
 * Janma essentials — birth vaara, tithi, nakshatra, yoga, and karana.
 */
import { useMemo, useState } from 'react'
import { buildJanmaPanchanga } from '../lib/janmaPanchanga'

const cell = {
  background: 'var(--highlight-bg)',
  border: '1px solid var(--card-border)',
  borderRadius: '0.65rem',
  padding: '0.65rem 0.75rem',
}

function Fact({ label, value, sub }) {
  return (
    <div style={cell}>
      <div style={{ fontSize: '0.68rem', letterSpacing: '0.04em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
        {label}
      </div>
      <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.15rem' }}>{value}</div>
      {sub ? <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.1rem' }}>{sub}</div> : null}
    </div>
  )
}

export default function JanmaEssentials({ chart }) {
  const data = useMemo(() => buildJanmaPanchanga(chart), [chart])
  const [open, setOpen] = useState(false)
  if (!data?.tithi?.name) return null

  const k = data.karana || {}
  const karanaTitle = [k.name, k.alias].filter(Boolean).join(' · ')

  return (
    <section
      className="rounded-xl mb-6 sm:mb-8"
      style={{
        background: 'var(--card-bg)',
        border: '1px solid var(--card-border)',
        boxShadow: 'var(--card-shadow)',
        padding: '16px 18px',
      }}
      aria-label="Janma essentials"
    >
      <h3 style={{
        fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)',
        textTransform: 'uppercase', letterSpacing: '0.07em', margin: '0 0 6px',
      }}>
        Janma essentials
      </h3>
      <p style={{ margin: '0 0 12px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        {data.note}
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <Fact label="Vaaram" value={data.vaara?.name} sub={`Lord ${data.vaara?.lord}`} />
        <Fact label="Janma tithi" value={`${data.tithi.paksha} ${data.tithi.name}`} />
        <Fact
          label="Janma nakshatra"
          value={data.nakshatra?.name}
          sub={[data.nakshatra?.pada ? `Pada ${data.nakshatra.pada}` : '', data.nakshatra?.lord].filter(Boolean).join(' · ')}
        />
        <Fact label="Janma yogam" value={data.yoga?.name} />
        <Fact
          label="Janma karanam"
          value={karanaTitle}
          sub={[k.name_ta, k.lord ? `Lord ${k.lord}` : ''].filter(Boolean).join(' · ')}
        />
        <Fact label="Karana lord" value={k.lord} sub={k.lord_ta} />
      </div>
      {k.practice?.en && (
        <p style={{ margin: '12px 0 0', fontSize: '0.8rem', lineHeight: 1.45, color: 'var(--text-secondary)' }}>
          <strong style={{ color: 'var(--text-primary)' }}>{k.animal}</strong>
          {k.animal_ta ? ` · ${k.animal_ta}` : ''}. {k.practice.en}
          {k.practice.ta ? <span style={{ display: 'block', marginTop: '0.25rem', color: 'var(--text-muted)' }}>{k.practice.ta}</span> : null}
        </p>
      )}
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
        {open ? 'Hide all 11 karanas' : 'All 11 karanas'}
      </button>
      {open && (
        <div style={{ overflowX: 'auto', marginTop: '0.6rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
            <thead>
              <tr>
                {['Karana', 'Lord', 'Animal', 'Practice'].map((h) => (
                  <th key={h} style={{ textAlign: 'left', padding: '6px 8px', borderBottom: '2px solid var(--orange)', color: 'var(--text-secondary)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(data.karanas || []).map((row) => (
                <tr key={row.name} style={{ background: row.name === k.name ? 'var(--highlight-bg)' : 'transparent' }}>
                  <td style={{ padding: '6px 8px', borderBottom: '1px solid var(--card-border)', color: 'var(--text-primary)' }}>
                    <strong>{row.name}</strong>
                    {row.alias ? ` · ${row.alias}` : ''}
                    <div style={{ color: 'var(--text-muted)' }}>{row.name_ta} · {row.kind}</div>
                  </td>
                  <td style={{ padding: '6px 8px', borderBottom: '1px solid var(--card-border)', color: 'var(--text-secondary)' }}>
                    {row.lord}
                    <div style={{ color: 'var(--text-muted)' }}>{row.deity}</div>
                  </td>
                  <td style={{ padding: '6px 8px', borderBottom: '1px solid var(--card-border)', color: 'var(--text-secondary)' }}>
                    {row.animal}
                    <div style={{ color: 'var(--text-muted)' }}>{row.animal_ta}</div>
                  </td>
                  <td style={{ padding: '6px 8px', borderBottom: '1px solid var(--card-border)', color: 'var(--text-secondary)', minWidth: '12rem' }}>
                    {row.practice?.en}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Lord and animal follow a Tamil karana practice table. Deity is the classical karana devata.
          </p>
        </div>
      )}
    </section>
  )
}
