/**
 * Prokerala-style South Indian 4×4 Ashtakavarga grid (BAV or SAV).
 */
import {
  BAV_RASI_LAYOUT,
  SAV_HOUSE_LAYOUT,
  SIGN_ABBR,
  binduStrength,
  houseForRasi,
  houseWiseToRasiWise,
} from '../lib/ashtakavargaGrid'

function GridCell({ slot, value, label, sub, strength, natural, isSav }) {
  const classes = [
    'av-pro-cell',
    `av-pro-cell--${slot}`,
    strength && `av-pro-cell--${strength}`,
    natural && 'av-pro-cell--natural',
  ].filter(Boolean).join(' ')

  return (
    <div className={classes}>
      {label && <span className="av-pro-cell__label">{label}</span>}
      <span className="av-pro-cell__value">{value}</span>
      {sub && <span className="av-pro-cell__sub">{sub}</span>}
      {isSav && strength && (
        <span className="av-pro-cell__hint">
          {value >= 30 ? 'Strong' : value >= 25 ? 'Good' : value >= 20 ? 'Avg' : 'Weak'}
        </span>
      )}
    </div>
  )
}

export function BavSouthGrid({
  houseWise,
  ascRasi,
  planetKey,
  planetLabel,
  planetRasi,
  total,
}) {
  const rasiChart = houseWiseToRasiWise(houseWise, ascRasi)

  return (
    <div className="av-pro-wrap">
      <div className="av-pro-grid av-pro-grid--bav">
        {BAV_RASI_LAYOUT.map(({ rasi, slot }) => {
          const val = rasiChart[rasi - 1]
          const natural = planetRasi === rasi
          return (
            <GridCell
              key={slot}
              slot={slot}
              value={val}
              label={SIGN_ABBR[rasi - 1]}
              sub={`H${houseForRasi(rasi, ascRasi)}`}
              strength={binduStrength(val, false)}
              natural={natural}
            />
          )
        })}
        <div className="av-pro-cell av-pro-cell--central">
          <div className="av-pro-cell__title">{planetLabel || planetKey}</div>
          <div className="av-pro-cell__total">Total: {total ?? rasiChart.reduce((a, b) => a + b, 0)}</div>
        </div>
      </div>
    </div>
  )
}

export function SavSouthGrid({ houseWise, total }) {
  const savTotal = total ?? houseWise.reduce((a, b) => a + b, 0)

  return (
    <div className="av-pro-wrap">
      <div className="av-pro-grid av-pro-grid--sav">
        {SAV_HOUSE_LAYOUT.map(({ house, slot }) => (
          <GridCell
            key={slot}
            slot={slot}
            value={houseWise[house - 1] ?? 0}
            label={`H${house}`}
            strength={binduStrength(houseWise[house - 1] ?? 0, true)}
            isSav
          />
        ))}
        <div className="av-pro-cell av-pro-cell--central">
          <div className="av-pro-cell__title">Sarva</div>
          <div className="av-pro-cell__title">Ashtakavarga</div>
          <div className="av-pro-cell__total">Total: {savTotal}</div>
        </div>
      </div>
    </div>
  )
}
