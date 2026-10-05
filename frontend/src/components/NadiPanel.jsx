/**
 * NadiPanel — twelve life questions read from a karaka planet's sign.
 * The board shows who sits where. The reason table says why. The timing table is the season.
 */
import { useEffect, useState } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'

const ROLE_LABEL = {
  happening: 'Happening',
  family: 'Family',
  behind: 'Already',
  follows: 'Follows',
  opposite: 'Opposite',
  'after Jupiter': 'After Jupiter',
}

function PlanetBoard({ board, significator }) {
  return (
    <div className="space-y-2">
      {significator && (
        <p className="text-sm" style={{ color: 'var(--text-primary)' }}>
          Significator: <span className="font-semibold">{significator}</span>
        </p>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2" aria-label="Natal planets by family">
        {board.map((family) => (
          <div key={family.name}>
            <p className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
              {family.name[0].toUpperCase() + family.name.slice(1)}
            </p>
            {family.signs_line && (
              <p className="text-xs" style={{ color: 'var(--text-muted)', overflowWrap: 'break-word' }}>{family.signs_line}</p>
            )}
            {family.available && (
              <p className="text-xs mb-1" style={{ color: 'var(--text-primary)', overflowWrap: 'break-word' }}>
                Available: {family.available}
              </p>
            )}
            <div className="grid grid-cols-3 gap-1">
              {family.signs.map((cell) => {
                const active = Boolean(cell.role)
                const planets = cell.planets || []
                return (
                  <div
                    key={cell.sign}
                    className="rounded-md px-1.5 py-1.5 min-w-0"
                    style={{
                      background: 'var(--card-bg)',
                      border: active ? '1px solid var(--orange)' : '1px solid var(--card-border)',
                    }}
                  >
                    <p className="text-xs font-semibold" style={{ color: 'var(--text-primary)', overflowWrap: 'break-word' }}>{cell.sign}</p>
                    {planets.length ? planets.map((planet) => (
                      <p key={planet.name} className="text-xs mt-0.5" style={{ color: 'var(--text-primary)', overflowWrap: 'anywhere' }}>
                        {planet.name}
                        {planet.significator ? ' · Significator' : ''}
                      </p>
                    )) : (
                      <p className="text-xs mt-0.5" style={{ color: 'var(--text-primary)', overflowWrap: 'anywhere' }}>{cell.label}</p>
                    )}
                    {cell.role && (
                      <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{ROLE_LABEL[cell.role] || cell.role}</p>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ReasonTable({ rows }) {
  return (
    <>
      <ul className="sm:hidden space-y-2" aria-label="Why each part of the chain is included">
        {rows.map((row) => (
          <li key={`${row.place}-${row.sign}-${row.planets}`} className="text-sm" style={{ color: 'var(--text-primary)', overflowWrap: 'anywhere' }}>
            <p className="font-semibold">{row.place} · {row.sign}</p>
            <p>{row.planets}</p>
            <p style={{ color: 'var(--text-muted)' }}>{row.reason}</p>
          </li>
        ))}
      </ul>
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full text-sm" style={{ borderCollapse: 'collapse' }}>
          <caption className="sr-only">Why each part of the chain is included</caption>
          <thead>
            <tr style={{ color: 'var(--text-muted)', textAlign: 'left' }}>
              <th className="py-1 pr-2 font-semibold">Place</th>
              <th className="py-1 pr-2 font-semibold">Sign</th>
              <th className="py-1 pr-2 font-semibold">Planets</th>
              <th className="py-1 font-semibold">Why</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.place}-${row.sign}-${row.planets}`} style={{ borderTop: '1px solid var(--card-border)', color: 'var(--text-primary)' }}>
                <td className="py-1.5 pr-2 align-top font-semibold">{row.place}</td>
                <td className="py-1.5 pr-2 align-top">{row.sign}</td>
                <td className="py-1.5 pr-2 align-top" style={{ overflowWrap: 'anywhere' }}>{row.planets}</td>
                <td className="py-1.5 align-top" style={{ overflowWrap: 'anywhere' }}>{row.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

function TimingTable({ rows }) {
  if (!rows?.length) {
    return (
      <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
        No Jupiter or Saturn season falls on these signs in the next 22 years.
      </p>
    )
  }
  return (
    <>
      <ul className="sm:hidden space-y-2" aria-label="Jupiter and Saturn seasons, and sharper Rahu and Ketu passes">
        {rows.map((row) => (
          <li key={`${row.kind}-${row.planet}-${row.when}`} className="text-sm" style={{ color: 'var(--text-primary)', overflowWrap: 'anywhere' }}>
            <p className="font-semibold">{row.planet} · {row.kind}</p>
            <p>{row.when}</p>
            <p style={{ color: 'var(--text-muted)' }}>{row.signs}</p>
          </li>
        ))}
      </ul>
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full text-sm" style={{ borderCollapse: 'collapse' }}>
          <caption className="sr-only">Jupiter and Saturn seasons, and sharper Rahu and Ketu passes</caption>
          <thead>
            <tr style={{ color: 'var(--text-muted)', textAlign: 'left' }}>
              <th className="py-1 pr-2 font-semibold">Planet</th>
              <th className="py-1 pr-2 font-semibold">Kind</th>
              <th className="py-1 pr-2 font-semibold">When</th>
              <th className="py-1 font-semibold">Signs</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.kind}-${row.planet}-${row.when}`} style={{ borderTop: '1px solid var(--card-border)', color: 'var(--text-primary)' }}>
                <td className="py-1.5 pr-2 align-top font-semibold">{row.planet}</td>
                <td className="py-1.5 pr-2 align-top">{row.kind}</td>
                <td className="py-1.5 pr-2 align-top">{row.when}</td>
                <td className="py-1.5 align-top">{row.signs}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

export default function NadiPanel({ chart, userId, gender = 'male', enabled = true }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [active, setActive] = useState('work')

  useEffect(() => {
    if (!chart || !enabled) return undefined
    let cancel = false
    setLoading(true)
    setError('')
    api.post('/nadi', chartPayload(chart, userId, { gender }))
      .then((res) => {
        if (!cancel) setData(res.data)
      })
      .catch((err) => {
        if (!cancel) setError(err.response?.data?.detail || 'Could not load the Nadi reading.')
      })
      .finally(() => {
        if (!cancel) setLoading(false)
      })
    return () => { cancel = true }
  }, [chart, userId, gender, enabled])

  if (!enabled) return null

  const reading = data?.readings?.find((row) => row.id === active) || data?.readings?.[0]

  return (
    <section className="space-y-3">
      <header>
        <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Nadi</h2>
        <p className="text-sm mt-1" style={{ color: 'var(--text-muted)', overflowWrap: 'break-word' }}>
          {data?.method || 'A reading from the planet that carries each question, not from a house number.'}
        </p>
      </header>

      {loading && !data && (
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Reading the chain…</p>
      )}
      {error && (
        <p className="text-sm" style={{ color: 'var(--orange)' }}>{error}</p>
      )}

      {reading && (
        <>
          <div className="flex flex-wrap gap-2" role="tablist" aria-label="Nadi questions">
            {data.readings.map((row) => {
              const selected = row.id === reading.id
              return (
                <button
                  key={row.id}
                  type="button"
                  role="tab"
                  aria-selected={selected}
                  onClick={() => setActive(row.id)}
                  className="px-3 py-2 rounded-full text-sm font-semibold min-h-[40px]"
                  style={{
                    background: selected ? 'var(--orange)' : 'var(--card-bg)',
                    color: selected ? 'var(--accent-dark)' : 'var(--text-primary)',
                    border: '1px solid var(--card-border)',
                  }}
                >
                  {row.label}
                </button>
              )
            })}
          </div>

          {reading.board && <PlanetBoard board={reading.board} significator={reading.significator} />}

          <article
            className="rounded-lg px-3 py-3 space-y-3"
            style={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)' }}
          >
            <div>
              <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Analysis</h3>
              <p className="text-sm mt-1" style={{ color: 'var(--text-primary)', overflowWrap: 'break-word' }}>
                {reading.analysis}
              </p>
              <p className="text-sm mt-2" style={{ color: 'var(--text-primary)', overflowWrap: 'break-word' }}>
                {reading.today}
              </p>
              <p className="text-sm mt-2" style={{ color: 'var(--text-primary)', overflowWrap: 'break-word' }}>
                {reading.season_status}
              </p>
            </div>

            {reading.reasons?.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>Why</h3>
                <ReasonTable rows={reading.reasons} />
              </div>
            )}

            <div>
              <h3 className="text-sm font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>When</h3>
              <TimingTable rows={reading.timing} />
            </div>

            <p className="text-xs" style={{ color: 'var(--text-muted)', overflowWrap: 'break-word' }}>
              {data.view}
            </p>
          </article>
        </>
      )}
    </section>
  )
}
