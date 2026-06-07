/**
 * SouthIndianChart.jsx
 * South Indian fixed-sign layout (4×4 grid, centre 2×2 merged).
 *
 * Props:
 *   title, subtitle       — centre cell text
 *   planetPositions       — { Planet: { sign_index, degree_in_sign, pada, retrograde, vargottama } }
 *   lagnaSignIndex        — 0-11, which sign has the ascendant marker
 *   navamsa               — boolean, use navamsa positions
 *   showDetails           — boolean (default false), show degree + pada in each badge
 *
 * Layout:
 *   Pisces(11) | Aries(0)  | Taurus(1)  | Gemini(2)
 *   Aquar(10)  |  [centre] |  [centre]  | Cancer(3)
 *   Capri(9)   |  [centre] |  [centre]  | Leo(4)
 *   Sagitt(8)  | Scorpio(7)| Libra(6)   | Virgo(5)
 */

const SIGN_ABBR  = ["Ar","Ta","Ge","Cn","Le","Vi","Li","Sc","Sg","Cp","Aq","Pi"]
const SIGN_SYM   = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]

const PLANET_SHORT = {
  Sun:"Su", Moon:"Mo", Mercury:"Me", Venus:"Ve", Mars:"Ma",
  Jupiter:"Ju", Saturn:"Sa", Rahu:"Ra", Ketu:"Ke",
}

const CRISIS_SET = new Set(["Mars","Rahu","Saturn","Ketu"])
const GROWTH_SET = new Set(["Jupiter","Venus"])

const PLANET_COLORS = {
  Sun:     { bg:"#fef3c7", fg:"#92400e" },
  Moon:    { bg:"#dbeafe", fg:"#1e40af" },
  Mercury: { bg:"#ede9fe", fg:"#5b21b6" },
  Venus:   { bg:"#dcfce7", fg:"#166534" },
  Mars:    { bg:"#fee2e2", fg:"#991b1b" },
  Jupiter: { bg:"#dcfce7", fg:"#166534" },
  Saturn:  { bg:"#fee2e2", fg:"#991b1b" },
  Rahu:    { bg:"#f5f3ff", fg:"#6d28d9" },
  Ketu:    { bg:"#fdf4ff", fg:"#7e22ce" },
}

// ── Planet badge — compact (no details) ─────────────────────────────────────
function PlanetBadgeCompact({ planet, retrograde, vargottama }) {
  const short = PLANET_SHORT[planet] || planet.slice(0,2)
  const col   = PLANET_COLORS[planet] || { bg:"#f1f5f9", fg:"#475569" }
  return (
    <span style={{
      display: "inline-block",
      borderRadius: "99px",
      padding: "1px 5px",
      fontSize: "0.66rem",
      fontWeight: 700,
      margin: "1px 1px 2px",
      background: col.bg,
      color: col.fg,
      lineHeight: 1.5,
      whiteSpace: "nowrap",
      border: vargottama ? "1.5px solid var(--orange)" : "1px solid transparent",
    }}>
      {retrograde && (
        <sup style={{ fontSize:"0.55rem", color:"var(--error-text)", fontWeight:900, marginRight:"1px" }}>℞</sup>
      )}
      {short}
      {vargottama && <sup style={{ fontSize:"0.5rem", color:"var(--orange)", marginLeft:"1px" }}>★</sup>}
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
      style={{ background: col.bg, color: col.fg, borderColor: vargottama ? 'var(--orange)' : 'var(--card-border)' }}
      title={`${planet} ${deg}° Pada ${pada || '—'}${retrograde ? ' Retrograde' : ''}`}
    >
      {retrograde && <span className="si-chart__badge-retro">℞</span>}
      <span className="si-chart__badge-name">{short}</span>
      <span className="si-chart__badge-deg">{deg}°</span>
      {pada != null && <span className="si-chart__badge-pada">P{pada}</span>}
      {vargottama && <span className="si-chart__badge-varga">★</span>}
    </span>
  )
}

// ── Chart cell ───────────────────────────────────────────────────────────────
function Cell({ signIdx, lagnaSignIdx, planetSignMap, retroSet, vargottamaSet, planetData, showDetails }) {
  const planets = planetSignMap[signIdx] || []
  const isLagna = signIdx === lagnaSignIdx
  const hasCrisis = planets.some(p => CRISIS_SET.has(p))
  const hasGrowth = planets.some(p => GROWTH_SET.has(p))

  let tone = ''
  if (hasCrisis && !hasGrowth) tone = 'si-chart__cell--crisis'
  else if (hasGrowth && !hasCrisis) tone = 'si-chart__cell--growth'

  return (
    <td className={[
      'si-chart__cell',
      showDetails && 'si-chart__cell--detail',
      isLagna && 'si-chart__cell--lagna',
      tone,
    ].filter(Boolean).join(' ')}>
      <span className="si-chart__sign" aria-hidden="true">
        {SIGN_SYM[signIdx]} {SIGN_ABBR[signIdx]}
      </span>
      {isLagna && <span className="si-chart__asc">ASC</span>}
      <div className="si-chart__planets">
        {planets.map(p => {
          const pd = planetData?.[p] || {}
          return showDetails ? (
            <PlanetBadgeDetail
              key={p}
              planet={p}
              retrograde={retroSet?.has(p)}
              vargottama={vargottamaSet?.has(p)}
              degreeInSign={pd.degree_in_sign}
              pada={pd.pada}
            />
          ) : (
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

// ── Main component ───────────────────────────────────────────────────────────
export default function SouthIndianChart({
  title,
  subtitle,
  planetPositions,
  lagnaSignIndex,
  navamsa     = false,
  showDetails = false,
}) {
  const planetSignMap = {}
  for (let i = 0; i < 12; i++) planetSignMap[i] = []

  const retroSet      = new Set()
  const vargottamaSet = new Set()

  Object.entries(planetPositions).forEach(([planet, data]) => {
    if (!data || typeof data !== 'object') return
    const idx = data.sign_index
    if (idx >= 0 && idx <= 11) planetSignMap[idx].push(planet)
    if (data.retrograde)  retroSet.add(planet)
    if (data.vargottama)  vargottamaSet.add(planet)
  })

  const cellProps = (signIdx) => ({
    signIdx,
    lagnaSignIdx:  lagnaSignIndex,
    planetSignMap,
    retroSet,
    vargottamaSet,
    planetData:    planetPositions,
    showDetails,
  })

  const centreStyle = {
    background: 'var(--chart-centre)',
    border: '1px solid var(--card-border)',
    textAlign: 'center',
    verticalAlign: 'middle',
    padding: showDetails ? '10px 8px' : '8px',
  }

  return (
    <div className={`si-chart-wrap${showDetails ? ' si-chart-wrap--detail' : ''}`}>
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
            <td colSpan={2} rowSpan={2} className="si-chart__centre" style={centreStyle}>
              <div className="si-chart__centre-title">{title}</div>
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
      {!showDetails && (
        <div className="si-chart__legend">
          <span style={{ color: 'var(--error-text)' }}>℞</span> Retrograde &nbsp;
          <span style={{ color: 'var(--orange-dark)' }}>★</span> Vargottama
        </div>
      )}
    </div>
  )
}
