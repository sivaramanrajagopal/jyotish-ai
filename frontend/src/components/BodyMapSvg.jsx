/**
 * BodyMapSvg — D3 health awareness body zones (color by risk).
 */
const ZONE_PATHS = {
  head: 'M 50 8 C 38 8 32 18 32 28 C 32 38 38 42 50 42 C 62 42 68 38 68 28 C 68 18 62 8 50 8 Z',
  neck: 'M 44 42 L 56 42 L 54 52 L 46 52 Z',
  chest: 'M 36 52 L 64 52 L 60 72 L 40 72 Z',
  torso: 'M 34 72 L 66 72 L 62 88 L 38 88 Z',
  abdomen: 'M 38 88 L 62 88 L 58 108 L 42 108 Z',
  arms: 'M 18 54 L 34 54 L 32 100 L 20 100 Z M 66 54 L 82 54 L 80 100 L 68 100 Z',
  pelvis: 'M 40 108 L 60 108 L 56 118 L 44 118 Z',
  legs: 'M 42 118 L 50 118 L 48 168 L 40 168 Z M 50 118 L 58 118 L 60 168 L 52 168 Z',
}

const RISK_FILL = {
  low: 'var(--hl-zone-low, rgba(34,197,94,0.25))',
  moderate: 'var(--hl-zone-moderate, rgba(245,158,11,0.45))',
  high: 'var(--hl-zone-high, rgba(239,68,68,0.55))',
}

const RISK_STROKE = {
  low: 'rgba(34,197,94,0.5)',
  moderate: 'rgba(245,158,11,0.8)',
  high: 'rgba(239,68,68,0.9)',
}

export default function BodyMapSvg({ regions = [], selectedZone, onSelectZone }) {
  const riskByZone = {}
  regions.forEach(r => {
    riskByZone[r.zone] = r.risk
  })

  const defaultRisk = 'low'

  return (
    <svg
      viewBox="0 0 100 180"
      className="hl-body-map"
      role="img"
      aria-label="Body map health awareness zones"
    >
      <ellipse cx="50" cy="90" rx="42" ry="78" className="hl-body-map__silhouette" />
      {Object.entries(ZONE_PATHS).map(([zone, d]) => {
        const risk = riskByZone[zone] || defaultRisk
        const selected = selectedZone === zone
        return (
          <path
            key={zone}
            d={d}
            fill={RISK_FILL[risk] || RISK_FILL.low}
            stroke={selected ? 'var(--orange)' : (RISK_STROKE[risk] || RISK_STROKE.low)}
            strokeWidth={selected ? 2 : 1}
            className="hl-body-map__zone"
            onClick={() => onSelectZone?.(zone)}
            style={{ cursor: onSelectZone ? 'pointer' : 'default' }}
          />
        )
      })}
    </svg>
  )
}
