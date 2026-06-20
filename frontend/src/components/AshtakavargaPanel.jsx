/**
 * AshtakavargaPanel — Prokerala-style South Indian BAV/SAV grids.
 */
import { useState, useEffect } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'
import { BavSouthGrid, SavSouthGrid } from './AshtakavargaSouthGrid'
import { BAV_CONTRIBUTOR_LABELS, RASHI_NAMES, houseWiseToRasiWise } from '../lib/ashtakavargaGrid'
import AvTriggerCard from './AvTriggerCard'

const PLANET_LABELS = {
  SUN: '☉ Sun', MOON: '☽ Moon', MARS: '♂ Mars', MERCURY: '☿ Mercury',
  JUPITER: '♃ Jupiter', VENUS: '♀ Venus', SATURN: '♄ Saturn', ASCENDANT: '⬆ Lagna',
}

const BAV_PLANETS = ['SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN', 'ASCENDANT']
const SAV_PLANETS = ['SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN']
const EXPECTED_TOTALS = {
  SUN: 48, MOON: 49, MARS: 39, MERCURY: 54, JUPITER: 56, VENUS: 52, SATURN: 39,
}

const TAB_LIST = [
  { key: 'sav', label: 'Sarva (SAV)' },
  ...BAV_PLANETS.filter(p => p !== 'ASCENDANT').map(p => ({ key: p, label: PLANET_LABELS[p] })),
  { key: 'ASCENDANT', label: PLANET_LABELS.ASCENDANT },
]

function houseForRasiNum(rasiNum, ascRasi) {
  for (let h = 1; h <= 12; h++) {
    if (((ascRasi - 1 + h - 1) % 12) + 1 === rasiNum) return h
  }
  return rasiNum
}

function MatrixTable({ planet, matrix, ascRasi, houseWise }) {
  if (!matrix?.length) return null
  const rasiWise = houseWiseToRasiWise(houseWise, ascRasi)

  return (
    <div className="av-pro-table-wrap">
      <h4 className="av-pro-table-title">{PLANET_LABELS[planet]} — contribution matrix</h4>
      <div className="av-pro-table-scroll">
        <table className="av-pro-table">
          <thead>
            <tr>
              <th>Rashi</th>
              {BAV_CONTRIBUTOR_LABELS.map(c => (
                <th key={c.key}>{c.short}</th>
              ))}
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {RASHI_NAMES.map((name, i) => {
              const h = houseForRasiNum(i + 1, ascRasi)
              return (
                <tr key={name}>
                  <td className="av-pro-table-rashi">{name}</td>
                  {matrix.map((row, ri) => (
                    <td key={ri} className={row[h - 1] ? 'av-pro-table-one' : ''}>
                      {row[h - 1] ? '1' : '·'}
                    </td>
                  ))}
                  <td className="av-pro-table-total">{rasiWise[i]}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function AshtakavargaPanel({ chart, userId, enabled = true }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [view, setView] = useState('sav')
  const [showMatrix, setShowMatrix] = useState(false)

  useEffect(() => {
    if (!chart || !enabled) return
    setLoading(true)
    setError('')
    api.post('/ashtakavarga', chartPayload(chart, userId))
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Could not load Ashtakavarga.'))
      .finally(() => setLoading(false))
  }, [chart, userId, enabled])

  if (!enabled) {
    return <div className="av-pro-loading" style={{ opacity: 0.6 }}>Open My Chart to load Ashtakavarga…</div>
  }

  if (loading) {
    return (
      <div className="av-pro-loading">Calculating Ashtakavarga…</div>
    )
  }
  if (error) {
    return <div className="av-pro-error">⚠️ {error}</div>
  }
  if (!data) return null

  const bav = data.bav || {}
  const sav = data.sav || {}
  const ascRasi = data.planetary_positions?.ASCENDANT
    ?? (data.lagna_sign_idx != null ? data.lagna_sign_idx + 1 : 1)
  const positions = data.planetary_positions || {}
  const matrix = data.matrix_8x8 || {}

  const activePlanet = view === 'sav' ? null : view
  const pData = activePlanet ? bav[activePlanet] : null

  return (
    <div className="av-pro-panel">
      <div className="av-pro-header">
        <h3 className="av-pro-heading">✦ Ashtakavarga</h3>
        <span className="av-pro-meta">
          SAV {sav.total ?? 0} / 337 · Lagna {data.lagna_sign}
          {data.rules === 'tamil' && ' · Tamil rules'}
        </span>
      </div>

      <div className="av-pro-tabs">
        {TAB_LIST.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            className={`av-pro-tab${view === key ? ' av-pro-tab--active' : ''}`}
            onClick={() => { setView(key); setShowMatrix(false) }}
          >
            {label}
          </button>
        ))}
      </div>

      {data.trigger_status?.available && (
        <AvTriggerCard status={data.trigger_status} />
      )}

      {view === 'sav' && (
        <div className="av-pro-section">
          <SavSouthGrid
            houseWise={sav.house_wise || []}
            ascRasi={ascRasi}
            total={sav.total}
          />
          <div className="av-pro-totals">
            <div className="av-pro-totals__title">Planet BAV totals</div>
            <div className="av-pro-totals__grid">
              {SAV_PLANETS.map(p => {
                const total = bav[p]?.total ?? 0
                const exp = EXPECTED_TOTALS[p]
                const ok = total === exp
                return (
                  <div key={p} className={`av-pro-total-row${ok ? ' av-pro-total-row--ok' : ''}`}>
                    <span>{PLANET_LABELS[p]}</span>
                    <strong>{total}</strong>
                    <span className="av-pro-total-exp">({exp})</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {activePlanet && pData && (
        <div className="av-pro-section">
          <BavSouthGrid
            houseWise={pData.house_wise || []}
            ascRasi={ascRasi}
            planetKey={activePlanet}
            planetLabel={PLANET_LABELS[activePlanet]}
            planetRasi={positions[activePlanet]}
            total={pData.total}
          />

          {pData.shodhya_pinda?.shodhya_pinda && (
            <div className="av-pro-pinda">
              <span>Shodhya Pinda: <strong>{pData.shodhya_pinda.shodhya_pinda}</strong></span>
              {pData.shodhya_pinda.trigger_nakshatra && (
                <span> · Trigger: {pData.shodhya_pinda.trigger_nakshatra}</span>
              )}
            </div>
          )}

          <button
            type="button"
            className="av-pro-matrix-toggle"
            onClick={() => setShowMatrix(v => !v)}
          >
            {showMatrix ? 'Hide' : 'Show'} 8×8 matrix
          </button>

          {showMatrix && (
            <MatrixTable
              planet={activePlanet}
              matrix={matrix[activePlanet]}
              ascRasi={ascRasi}
              houseWise={pData.house_wise}
            />
          )}
        </div>
      )}
    </div>
  )
}
