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
      border: vargottama ? "1.5px solid #f59e0b" : "1px solid transparent",
    }}>
      {retrograde && (
        <sup style={{ fontSize:"0.55rem", color:"#ef4444", fontWeight:900, marginRight:"1px" }}>℞</sup>
      )}
      {short}
      {vargottama && <sup style={{ fontSize:"0.5rem", color:"#f59e0b", marginLeft:"1px" }}>★</sup>}
    </span>
  )
}

// ── Planet badge — detailed (degree + pada + retrograde prominent) ──────────
function PlanetBadgeDetail({ planet, retrograde, vargottama, degreeInSign, pada }) {
  const short = PLANET_SHORT[planet] || planet.slice(0,2)
  const col   = PLANET_COLORS[planet] || { bg:"#f1f5f9", fg:"#475569" }
  const deg   = typeof degreeInSign === 'number' ? degreeInSign.toFixed(1) : '—'

  return (
    <div style={{
      display: "inline-flex",
      flexDirection: "column",
      alignItems: "center",
      borderRadius: "6px",
      padding: "3px 5px 2px",
      fontSize: "0.62rem",
      fontWeight: 700,
      margin: "2px 2px 2px",
      background: col.bg,
      color: col.fg,
      lineHeight: 1.3,
      border: vargottama ? "1.5px solid #f59e0b" : "1px solid rgba(0,0,0,0.08)",
      minWidth: "30px",
      position: "relative",
    }}>
      {/* Retrograde badge — shown prominently on top */}
      {retrograde && (
        <span style={{
          position: "absolute",
          top: "-7px",
          right: "-5px",
          background: "#ef4444",
          color: "#fff",
          fontSize: "0.48rem",
          fontWeight: 900,
          borderRadius: "99px",
          padding: "0px 3px",
          lineHeight: 1.6,
          zIndex: 1,
          border: "1px solid #fef3c7",
        }}>℞</span>
      )}
      {/* Vargottama star */}
      {vargottama && (
        <span style={{
          position: "absolute",
          top: "-7px",
          left: "-4px",
          color: "#f59e0b",
          fontSize: "0.55rem",
          fontWeight: 900,
        }}>★</span>
      )}
      {/* Planet short name */}
      <span style={{ fontSize: "0.7rem", fontWeight: 800 }}>{short}</span>
      {/* Degree */}
      <span style={{ fontSize: "0.55rem", opacity: 0.85, fontWeight: 600 }}>{deg}°</span>
      {/* Pada */}
      {pada && (
        <span style={{
          fontSize: "0.5rem",
          background: "rgba(0,0,0,0.12)",
          borderRadius: "3px",
          padding: "0 3px",
          marginTop: "1px",
          fontWeight: 700,
        }}>P{pada}</span>
      )}
    </div>
  )
}

// ── Chart cell ───────────────────────────────────────────────────────────────
function Cell({ signIdx, lagnaSignIdx, planetSignMap, retroSet, vargottamaSet, planetData, showDetails }) {
  const planets   = planetSignMap[signIdx] || []
  const isLagna   = signIdx === lagnaSignIdx
  const hasCrisis = planets.some(p => CRISIS_SET.has(p))
  const hasGrowth = planets.some(p => GROWTH_SET.has(p))

  let bg = "var(--chart-cell-bg)"
  if (hasCrisis && !hasGrowth) bg = "var(--chart-cell-crisis)"
  else if (hasGrowth && !hasCrisis) bg = "var(--chart-cell-growth)"

  const lagnaGrad = isLagna
    ? ", linear-gradient(45deg, transparent 46%, #FF9900 47%, #FF9900 53%, transparent 54%)"
    : ""

  return (
    <td style={{
      background: `${bg}${lagnaGrad}`,
      border: "1px solid var(--card-border)",
      padding: "4px 3px 3px",
      verticalAlign: "top",
      width: "25%",
      position: "relative",
    }}>
      {/* Sign label top-right */}
      <div style={{
        fontSize: "0.5rem",
        color: "var(--text-muted)",
        textAlign: "right",
        lineHeight: 1,
        marginBottom: "2px",
        userSelect: "none",
      }}>
        {SIGN_SYM[signIdx]} {SIGN_ABBR[signIdx]}
      </div>

      {/* ASC label */}
      {isLagna && (
        <div style={{
          fontSize: "0.48rem", fontWeight: 700, color: "#FFFFFF",
          background: "#FF9900", borderRadius: "3px",
          padding: "0 3px", display: "inline-block", marginBottom: "2px",
        }}>ASC</div>
      )}

      {/* Planet badges */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "1px" }}>
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
    background: "var(--chart-centre)",
    border: "1px solid var(--card-border)",
    textAlign: "center",
    verticalAlign: "middle",
    padding: "8px",
  }

  return (
    <div style={{ width: "100%" }}>
      <table style={{
        borderCollapse: "collapse",
        width: "100%",
        tableLayout: "fixed",
        fontFamily: "'Inter', system-ui, sans-serif",
      }}>
        <tbody>
          <tr>
            <Cell {...cellProps(11)} />
            <Cell {...cellProps(0)} />
            <Cell {...cellProps(1)} />
            <Cell {...cellProps(2)} />
          </tr>
          <tr>
            <Cell {...cellProps(10)} />
            <td colSpan={2} rowSpan={2} style={centreStyle}>
              <div style={{ color:"var(--orange-dark)", fontWeight:700, fontSize:"0.85rem" }}>{title}</div>
              {subtitle && (
                <div style={{ color:"var(--text-muted)", fontSize:"0.6rem", marginTop:"4px", lineHeight:1.4 }}>
                  {subtitle}
                </div>
              )}
              {showDetails && (
                <div style={{ marginTop:"8px", fontSize:"0.5rem", color:"var(--text-muted)", lineHeight:1.8 }}>
                  <div><span style={{color:"var(--error-text)"}}>℞</span> Retrograde</div>
                  <div><span style={{color:"var(--orange-dark)"}}>★</span> Vargottama</div>
                  <div>15.3° = degree</div>
                  <div>P2 = pada</div>
                </div>
              )}
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
        <div style={{ fontSize:"0.55rem", color:"var(--text-muted)", marginTop:"4px", textAlign:"right" }}>
          <span style={{color:"var(--error-text)"}}>℞</span> Retrograde &nbsp;
          <span style={{color:"var(--orange-dark)"}}>★</span> Vargottama
        </div>
      )}
    </div>
  )
}
