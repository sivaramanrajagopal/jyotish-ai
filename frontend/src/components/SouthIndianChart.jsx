/**
 * SouthIndianChart.jsx
 * South Indian fixed-sign layout (4×4 grid, centre 2×2 merged).
 */

import { isPlanetRetrograde } from '../lib/planetRetrograde'

/**
 * Props:
 *   title, subtitle       — centre cell text
 *   planetPositions       — { Planet: { sign_index, degree_in_sign, pada, retrograde, vargottama } }
 *   lagnaSignIndex        — 0-11, which sign has the ascendant marker
 *   navamsa               — boolean, use navamsa positions
 *   showDetails           — boolean (default false), show degree + pada in each badge
 *   variant               — 'default' | 'classic' (classic = traditional Tamil house labels)
 *   chartKind             — 'natal' | 'transit' | 'prashna' (legend + centre label)
 *
 * Layout:
 *   Pisces(11) | Aries(0)  | Taurus(1)  | Gemini(2)
 *   Aquar(10)  |  [centre] |  [centre]  | Cancer(3)
 *   Capri(9)   |  [centre] |  [centre]  | Leo(4)
 *   Sagitt(8)  | Scorpio(7)| Libra(6)   | Virgo(5)
 */

const SIGN_ABBR = ['Ar', 'Ta', 'Ge', 'Cn', 'Le', 'Vi', 'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi']
const SIGN_SYM = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']

/** Tamil rashi names — house 1 (Mesha) through 12 (Meena) */
const RASHI_TAMIL = [
  'மேஷம்', 'ரிஷபம்', 'மிதுனம்', 'கடகம்', 'சிம்மம்', 'கன்னி', 'துலாம்', 'விருச்சிகம்', 'தனுசு', 'மகரம்', 'கும்பம்', 'மீனம்',
]

const PLANET_SHORT = {
  Sun: 'Su', Moon: 'Mo', Mercury: 'Me', Venus: 'Ve', Mars: 'Ma',
  Jupiter: 'Ju', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
}

const CRISIS_SET = new Set(['Mars', 'Rahu', 'Saturn', 'Ketu'])
const GROWTH_SET = new Set(['Jupiter', 'Venus'])

const PLANET_COLORS = {
  Sun:     { bg: '#fef3c7', fg: '#92400e' },
  Moon:    { bg: '#dbeafe', fg: '#1e40af' },
  Mercury: { bg: '#ede9fe', fg: '#5b21b6' },
  Venus:   { bg: '#dcfce7', fg: '#166534' },
  Mars:    { bg: '#fee2e2', fg: '#991b1b' },
  Jupiter: { bg: '#dcfce7', fg: '#166534' },
  Saturn:  { bg: '#fee2e2', fg: '#991b1b' },
  Rahu:    { bg: '#f5f3ff', fg: '#6d28d9' },
  Ketu:    { bg: '#fdf4ff', fg: '#7e22ce' },
}

function nakshatraAbbr(name) {
  if (!name || typeof name !== 'string') return ''
  return name.length <= 4 ? name : name.substring(0, 3)
}

// ── Planet badge — compact (no details) ─────────────────────────────────────
function PlanetBadgeCompact({ planet, retrograde, vargottama }) {
  const short = PLANET_SHORT[planet] || planet.slice(0, 2)
  const col = PLANET_COLORS[planet] || { bg: '#f1f5f9', fg: '#475569' }
  return (
    <span style={{
      display: 'inline-block',
      borderRadius: '99px',
      padding: '1px 5px',
      fontSize: '0.66rem',
      fontWeight: 700,
      margin: '1px 1px 2px',
      background: col.bg,
      color: col.fg,
      lineHeight: 1.5,
      whiteSpace: 'nowrap',
      border: vargottama ? '1.5px solid var(--chart-lagna-accent)' : '1px solid transparent',
    }}>
      {short}
      {retrograde && <sup className="retro-sup-r">R</sup>}
      {vargottama && <sup style={{ fontSize: '0.5rem', color: 'var(--chart-lagna-accent)', marginLeft: '1px' }}>★</sup>}
    </span>
  )
}

// ── Planet badge — detailed (degree + pada, single-line for transit charts) ─
function PlanetBadgeDetail({ planet, retrograde, vargottama, degreeInSign, pada }) {
  const short = PLANET_SHORT[planet] || planet.slice(0, 2)
  const col = PLANET_COLORS[planet] || { bg: '#f1f5f9', fg: '#475569' }
  const deg = typeof degreeInSign === 'number' ? degreeInSign.toFixed(1) : '—'

  return (
    <span
      className="si-chart__badge si-chart__badge--detail"
      style={{ background: col.bg, color: col.fg, borderColor: vargottama ? 'var(--chart-lagna-accent)' : 'var(--card-border)' }}
      title={`${planet} ${deg}° Pada ${pada || '—'}${retrograde ? ' Retrograde' : ''}`}
    >
      <span className="si-chart__badge-name">
        {short}
        {retrograde && <sup className="retro-sup-r">R</sup>}
      </span>
      <span className="si-chart__badge-deg">{deg}°</span>
      {pada != null && <span className="si-chart__badge-pada">P{pada}</span>}
      {vargottama && <span className="si-chart__badge-varga">★</span>}
    </span>
  )
}

function formatNakshatraLine(nakshatra, pada, useFullName = true) {
  if (!nakshatra && pada == null) return null
  const name = useFullName ? nakshatra : nakshatraAbbr(nakshatra)
  if (!name) return pada != null ? `P${pada}` : null
  return pada != null ? `${name} · P${pada}` : name
}

// ── Planet badge — classic stacked row (traditional readability) ───────────────
function PlanetBadgeClassic({ planet, retrograde, vargottama, degreeInSign, pada, nakshatra, house, showHouse }) {
  const short = PLANET_SHORT[planet] || planet.slice(0, 2)
  const col = PLANET_COLORS[planet] || { bg: '#f1f5f9', fg: '#475569' }
  const deg = typeof degreeInSign === 'number' ? degreeInSign.toFixed(1) : '—'
  const nakLine = formatNakshatraLine(nakshatra, pada, true)

  return (
    <div
      className="si-chart__classic-planet"
      style={{ background: col.bg, color: col.fg, borderColor: vargottama ? 'var(--chart-lagna-accent)' : 'var(--card-border)' }}
      title={`${planet} ${deg}° ${nakshatra || ''}${pada != null ? ` P${pada}` : ''}${house != null ? ` H${house}` : ''}${retrograde ? ' ℞' : ''}`}
    >
      <div className="si-chart__classic-planet-row">
        <span className="si-chart__classic-planet-name">
          {short}
          {retrograde && <sup className="retro-sup-r">R</sup>}
        </span>
        <span className="si-chart__classic-planet-deg">{deg}°</span>
        {vargottama && <span className="si-chart__classic-planet-varga">★</span>}
      </div>
      {showHouse && house != null && (
        <div className="si-chart__classic-planet-house">H{house}</div>
      )}
      {nakLine && (
        <div className="si-chart__classic-planet-nak">{nakLine}</div>
      )}
    </div>
  )
}

// ── Chart cell ───────────────────────────────────────────────────────────────
function Cell({
  signIdx, lagnaSignIdx, planetSignMap, retroSet, vargottamaSet, planetData,
  showDetails, variant, chartKind = 'natal',
}) {
  const planets = planetSignMap[signIdx] || []
  const isLagna = signIdx === lagnaSignIdx
  const isClassic = variant === 'classic'
  const houseNum = signIdx + 1
  const hasCrisis = planets.some(p => CRISIS_SET.has(p))
  const hasGrowth = planets.some(p => GROWTH_SET.has(p))

  let tone = ''
  if (hasCrisis && !hasGrowth) tone = 'si-chart__cell--crisis'
  else if (hasGrowth && !hasCrisis) tone = 'si-chart__cell--growth'

  const useDetail = showDetails && !isClassic
  const useClassicDetail = showDetails && isClassic
  const showHouseOnPlanet = isClassic && chartKind === 'transit'

  return (
    <td className={[
      'si-chart__cell',
      (showDetails || isClassic) && 'si-chart__cell--detail',
      isClassic && 'si-chart__cell--classic',
      isLagna && 'si-chart__cell--lagna',
      isLagna && isClassic && 'si-chart__cell--lagna-classic',
      tone,
    ].filter(Boolean).join(' ')}>
      {isClassic ? (
        <>
          <div className="si-chart__classic-house">{houseNum}</div>
          <div className="si-chart__classic-rashi">{RASHI_TAMIL[signIdx]}</div>
          {isLagna && (
            <span className="si-chart__lagna-badge">Lagna ↑</span>
          )}
        </>
      ) : (
        <>
          <span className={`si-chart__sign${isLagna ? ' si-chart__sign--lagna' : ''}`} aria-hidden="true">
            {SIGN_SYM[signIdx]} {SIGN_ABBR[signIdx]}
          </span>
          {isLagna && <span className="si-chart__asc">Asc</span>}
        </>
      )}

      <div className={`si-chart__planets${isClassic ? ' si-chart__planets--classic' : ''}`}>
        {planets.map(p => {
          const pd = planetData?.[p] || {}
          if (useClassicDetail) {
            return (
              <PlanetBadgeClassic
                key={p}
                planet={p}
                retrograde={retroSet?.has(p)}
                vargottama={vargottamaSet?.has(p)}
                degreeInSign={pd.degree_in_sign}
                pada={pd.pada}
                nakshatra={pd.nakshatra}
                house={pd.house}
                showHouse={showHouseOnPlanet}
              />
            )
          }
          if (useDetail) {
            return (
              <PlanetBadgeDetail
                key={p}
                planet={p}
                retrograde={retroSet?.has(p)}
                vargottama={vargottamaSet?.has(p)}
                degreeInSign={pd.degree_in_sign}
                pada={pd.pada}
              />
            )
          }
          return (
            <PlanetBadgeCompact
              key={p}
              planet={p}
              retrograde={retroSet?.has(p)}
              vargottama={vargottamaSet?.has(p)}
            />
          )
        })}
      </div>
    </td>
  )
}

function ClassicLegend({ chartKind = 'natal' }) {
  const lagnaNote = chartKind === 'transit'
    ? 'Ascendant at chart time (noon local for transits)'
    : 'Rising sign at birth (most important reference point)'
  const vargaNote = chartKind === 'transit'
    ? null
    : 'Vargottama (same sign in D1 and D9)'

  return (
    <details className="si-chart__classic-legend">
      <summary>How to read this chart</summary>
      <ul>
        <li><strong>Lagna ↑</strong> — {lagnaNote}</li>
        <li><sup className="retro-sup-r">R</sup> — retrograde planet</li>
        {vargaNote && (
          <li><span style={{ color: 'var(--chart-lagna-accent)' }}>★</span> — {vargaNote}</li>
        )}
        <li>Numbers 1–12 are fixed signs (Mesha → Meena)</li>
        {chartKind === 'transit' && (
          <li>Each planet shows degree, nakshatra · pada, and house from Ascendant</li>
        )}
        {chartKind === 'natal' && (
          <li>Each planet shows degree and nakshatra · pada</li>
        )}
      </ul>
    </details>
  )
}

// ── Main component ───────────────────────────────────────────────────────────
export default function SouthIndianChart({
  title,
  subtitle,
  planetPositions,
  lagnaSignIndex,
  navamsa = false,
  showDetails = false,
  variant = 'default',
  chartKind = 'natal',
}) {
  const isClassic = variant === 'classic'
  const planetSignMap = {}
  for (let i = 0; i < 12; i++) planetSignMap[i] = []

  const retroSet = new Set()
  const vargottamaSet = new Set()

  Object.entries(planetPositions).forEach(([planet, data]) => {
    if (!data || typeof data !== 'object') return
    const idx = data.sign_index
    if (idx >= 0 && idx <= 11) planetSignMap[idx].push(planet)
    if (isPlanetRetrograde(planet, data)) retroSet.add(planet)
    if (data.vargottama) vargottamaSet.add(planet)
  })

  const cellProps = (signIdx) => ({
    signIdx,
    lagnaSignIdx: lagnaSignIndex,
    planetSignMap,
    retroSet,
    vargottamaSet,
    planetData: planetPositions,
    showDetails,
    variant,
    chartKind,
  })

  const centreStyle = {
    background: 'var(--chart-centre)',
    border: isClassic ? '2px solid var(--chart-lagna-accent)' : '1px solid var(--card-border)',
    textAlign: 'center',
    verticalAlign: 'middle',
    padding: showDetails || isClassic ? '10px 8px' : '8px',
  }

  return (
    <div className={[
      'si-chart-wrap',
      showDetails && 'si-chart-wrap--detail',
      isClassic && 'si-chart-wrap--classic',
    ].filter(Boolean).join(' ')}>
      <table className="si-chart">
        <tbody>
          <tr>
            <Cell {...cellProps(11)} />
            <Cell {...cellProps(0)} />
            <Cell {...cellProps(1)} />
            <Cell {...cellProps(2)} />
          </tr>
          <tr>
            <Cell {...cellProps(10)} />
            <td colSpan={2} rowSpan={2} className={`si-chart__centre${isClassic ? ' si-chart__centre--classic' : ''}`} style={centreStyle}>
              <div className="si-chart__centre-title">{title}</div>
              {isClassic && chartKind === 'transit' && (
                <div className="si-chart__centre-tamil">கோசாரம்</div>
              )}
              {isClassic && chartKind === 'natal' && navamsa && (
                <div className="si-chart__centre-tamil">நவாம்சம்</div>
              )}
              {isClassic && chartKind === 'natal' && !navamsa && (
                <div className="si-chart__centre-tamil">ராசி சக்கரம்</div>
              )}
              {isClassic && chartKind === 'prashna' && (
                <div className="si-chart__centre-tamil">பிரஷ்னா</div>
              )}
              {subtitle && <div className="si-chart__centre-sub">{subtitle}</div>}
            </td>
            <Cell {...cellProps(3)} />
          </tr>
          <tr>
            <Cell {...cellProps(9)} />
            <Cell {...cellProps(4)} />
          </tr>
          <tr>
            <Cell {...cellProps(8)} />
            <Cell {...cellProps(7)} />
            <Cell {...cellProps(6)} />
            <Cell {...cellProps(5)} />
          </tr>
        </tbody>
      </table>
      {isClassic && showDetails && <ClassicLegend chartKind={chartKind} />}
      {!showDetails && !isClassic && (
        <div className="si-chart__legend">
          <sup className="retro-sup-r">R</sup> Retrograde &nbsp;
          <span style={{ color: 'var(--chart-lagna-accent)' }}>★</span> Vargottama
        </div>
      )}
    </div>
  )
}
