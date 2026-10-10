/**
 * ReadingPanel — one sitting, spoken in order after the chart is calculated.
 */
import { useEffect, useState } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'

function Movement({ index, title, children }) {
  return (
    <section className="space-y-2">
      <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
        {index} · {title}
      </h3>
      {children}
    </section>
  )
}

function Said({ children }) {
  return (
    <p className="text-sm" style={{ color: 'var(--text-primary)', overflowWrap: 'break-word' }}>
      {children}
    </p>
  )
}

const STHULA_MEANING = {
  Deepta: 'Bright, strongly expressive',
  Sthamitha: 'Stable in its own strength',
  Muditha: 'Comfortable, supported',
  Santha: 'Calm, moderate output',
  Sakta: 'Constrained, often by retrograde',
  Heenasakstha: 'Weakened capacity',
  Deena: 'Distressed, an inimical setting',
  Peethya: 'At the edge of the sign, unstable',
  Peeda: 'Pressured by fast motion',
  Vikala: 'Impaired by combustion',
  Kala: 'Dark, debilitated',
}

const SUKSHMA_MEANING = {
  Sayana: 'Resting, slow to deliver',
  Upaveshana: 'Seated, preparing',
  Netrapani: 'Watching, strategic',
  Prakasha: 'Fully lit, peak output',
  Gamana: 'Moving, unstable',
  Aagamana: 'Arriving, productive',
  Aasthani: 'Settled high, peak output',
  Aagama: 'Coming in, material gains',
  Bhoji: 'Enjoying, high yield',
  Nritya: 'Active, productive',
  Kauthuka: 'Curious, moderate',
  Nidra: 'Asleep, dormant',
}

function Condition({ row }) {
  const gross = STHULA_MEANING[row.condition]
  const subtle = SUKSHMA_MEANING[row.sukshma]
  return (
    <div style={{ overflowWrap: 'anywhere' }}>
      <p>
        {row.condition || '—'}
        {row.net != null ? ` · ${row.net}` : ''}
      </p>
      {gross && <p style={{ color: 'var(--text-muted)' }}>Sthula: {gross}</p>}
      {row.sukshma && (
        <p style={{ color: 'var(--text-muted)' }}>
          Sukshma {row.sukshma}{subtle ? `: ${subtle}` : ''}
        </p>
      )}
    </div>
  )
}

function VoiceTable({ rows }) {
  return (
    <>
      <ul className="md:hidden space-y-2" aria-label="Strength held against strength needed, with condition">
        {rows.map((row) => (
          <li
            key={row.planet}
            className="rounded-md px-2.5 py-2 text-sm"
            style={{
              color: 'var(--text-primary)',
              background: 'var(--surface-muted)',
              border: '1px solid var(--card-border)',
              overflowWrap: 'anywhere',
            }}
          >
            <p className="font-semibold">{row.planet}{row.short ? ' · short' : ''}</p>
            <p style={{ color: 'var(--text-muted)' }}>
              Held {row.held} · needed {row.needed}
            </p>
            <Condition row={row} />
          </li>
        ))}
      </ul>
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-sm" style={{ borderCollapse: 'collapse' }}>
          <caption className="sr-only">Strength held against strength needed, with condition</caption>
          <thead>
            <tr style={{ color: 'var(--text-muted)', textAlign: 'left' }}>
              <th className="py-1 pr-2 font-semibold">Planet</th>
              <th className="py-1 pr-2 font-semibold">Held</th>
              <th className="py-1 pr-2 font-semibold">Needed</th>
              <th className="py-1 font-semibold">Condition</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.planet} style={{ borderTop: '1px solid var(--card-border)', color: 'var(--text-primary)' }}>
                <td className="py-1.5 pr-2 align-top font-semibold">{row.planet}{row.short ? ' · short' : ''}</td>
                <td className="py-1.5 pr-2 align-top">{row.held}</td>
                <td className="py-1.5 pr-2 align-top">{row.needed}</td>
                <td className="py-1.5 align-top"><Condition row={row} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

export default function ReadingPanel({ chart, userId, gender = 'male', enabled = true }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [openIds, setOpenIds] = useState([])

  useEffect(() => {
    if (!chart || !enabled) return undefined
    let cancel = false
    setLoading(true)
    setError('')
    api.post('/reading', chartPayload(chart, userId, { gender }))
      .then((res) => {
        if (cancel) return
        setData(res.data)
        setOpenIds((res.data.life || []).filter((row) => row.open).map((row) => row.id))
      })
      .catch((err) => {
        if (!cancel) setError(err.response?.data?.detail || 'Could not load the reading.')
      })
      .finally(() => {
        if (!cancel) setLoading(false)
      })
    return () => { cancel = true }
  }, [chart, userId, gender, enabled])

  if (!enabled) return null

  const toggle = (id) => {
    setOpenIds((current) => (
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    ))
  }

  return (
    <section className="space-y-4 pb-16 md:pb-0">
      <header>
        <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Reading</h2>
        <p className="text-sm mt-1" style={{ color: 'var(--text-muted)', overflowWrap: 'break-word' }}>
          {data?.who?.born ? `${data.who.born}${data.who.place ? ` · ${data.who.place}` : ''}. ` : ''}
          One sitting from this chart. Each part is said in order.
        </p>
      </header>

      {loading && !data && (
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Reading the chart…</p>
      )}
      {error && (
        <p className="text-sm" style={{ color: 'var(--orange)' }}>{error}</p>
      )}

      {data && (
        <div
          className="rounded-lg px-3 py-3 space-y-4"
          style={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)' }}
        >
          <Movement index="1" title="Who this is">
            <Said>{data.who.sentence}</Said>
          </Movement>

          <Movement index="2" title="Who can speak">
            <Said>{data.voice.sentence}</Said>
            {data.voice.rows?.length > 0 && <VoiceTable rows={data.voice.rows} />}
          </Movement>

          <Movement index="3" title="The chapter now">
            <Said>{data.chapter.sentence}</Said>
          </Movement>

          <Movement index="4" title="What is pressing">
            <Said>{data.pressing.sentence}</Said>
            {data.pressing.houses?.length > 0 && (
              <ul className="space-y-1">
                {data.pressing.houses.map((house) => (
                  <li key={house.house} className="text-sm" style={{ color: 'var(--text-primary)', overflowWrap: 'anywhere' }}>
                    {house.line}
                  </li>
                ))}
              </ul>
            )}
          </Movement>

          <Movement index="5" title="The life, one question at a time">
            <Said>
              Open seasons are unfolded. A closed season stays one line until you open it.
            </Said>
            <ul className="space-y-2">
              {(data.life || []).map((row) => {
                const expanded = openIds.includes(row.id)
                return (
                  <li key={row.id}>
                    <button
                      type="button"
                      aria-expanded={expanded}
                      onClick={() => toggle(row.id)}
                      className="w-full text-left rounded-md px-2.5 py-2.5 min-h-[44px]"
                      style={{
                        background: 'var(--surface-muted)',
                        border: '1px solid var(--card-border)',
                        color: 'var(--text-primary)',
                      }}
                    >
                      <span className="text-sm font-semibold" style={{ overflowWrap: 'anywhere' }}>
                        {row.label} · {row.open ? 'Open' : 'Closed'}
                      </span>
                      <span className="block text-sm" style={{ overflowWrap: 'anywhere' }}>{row.when}</span>
                    </button>
                    {expanded && (
                      <div className="px-2 py-2 space-y-1">
                        <Said>{row.analysis}</Said>
                        <Said>{row.today}</Said>
                        <Said>{row.season_status}</Said>
                        {row.house?.lines?.length > 0 && (
                          <div className="space-y-1 pt-1">
                            <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                              How this house gives
                            </p>
                            {row.house.lines.map((line) => (
                              <Said key={line}>{line}</Said>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </li>
                )
              })}
            </ul>
          </Movement>

          <Movement index="6" title="What snags">
            <Said>{data.snags.sentence}</Said>
            {data.snags.alerts?.length > 0 && (
              <ul className="space-y-1">
                {data.snags.alerts.map((alert) => (
                  <li key={`${alert.planet}-${alert.note}`} className="text-sm" style={{ color: 'var(--text-primary)', overflowWrap: 'anywhere' }}>
                    <span className="font-semibold">{alert.planet}. </span>{alert.note}
                  </li>
                ))}
              </ul>
            )}
          </Movement>

          <Movement index="7" title="What comes next">
            <Said>{data.next.sentence}</Said>
          </Movement>
        </div>
      )}
    </section>
  )
}
