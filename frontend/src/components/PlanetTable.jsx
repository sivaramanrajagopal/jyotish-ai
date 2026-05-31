/**
 * PlanetTable.jsx
 * Full planet details table: sign, house, degree, nakshatra, lord, pada, D9 sign, retro
 */

const PLANET_ORDER = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]

const PLANET_SYMBOLS = {
  Sun:"☉", Moon:"☽", Mars:"♂", Mercury:"☿",
  Jupiter:"♃", Venus:"♀", Saturn:"♄", Rahu:"☊", Ketu:"☋",
}

const CRISIS_SET = new Set(["Mars","Rahu","Saturn","Ketu"])
const GROWTH_SET = new Set(["Jupiter","Venus"])

function planetRowColor(planet) {
  if (GROWTH_SET.has(planet)) return "rgba(220,252,231,0.06)"
  if (CRISIS_SET.has(planet)) return "rgba(254,226,226,0.06)"
  if (planet === "Sun")  return "rgba(254,243,199,0.06)"
  if (planet === "Moon") return "rgba(219,234,254,0.06)"
  return "transparent"
}

export default function PlanetTable({ planetPositions, navamsaPositions, ascendant }) {
  return (
    <div style={{ overflowX:"auto" }}>
      <table style={{
        width:"100%",
        borderCollapse:"collapse",
        fontFamily:"'Inter',system-ui,sans-serif",
        fontSize:"0.78rem",
        color:"#fef3c7",
      }}>
        <thead>
          <tr style={{ background:"rgba(251,191,36,0.1)", color:"rgba(251,191,36,0.6)", textAlign:"left" }}>
            <th style={th}>Planet</th>
            <th style={th}>Sign</th>
            <th style={th}>Sign Lord</th>
            <th style={{...th, textAlign:"right"}}>Degree</th>
            <th style={{...th, textAlign:"center"}}>House</th>
            <th style={th}>Nakshatra</th>
            <th style={th}>Nak. Lord</th>
            <th style={{...th, textAlign:"center"}}>Pada</th>
            <th style={th}>D9 Sign</th>
            <th style={{...th, textAlign:"center"}}>Retro</th>
          </tr>
        </thead>
        <tbody>
          {/* Ascendant row */}
          <tr style={{ background:"rgba(251,191,36,0.12)", borderBottom:"1px solid rgba(251,191,36,0.15)" }}>
            <td style={td}>
              <span style={{ fontWeight:600, color:"#fbbf24" }}>⬆ Ascendant</span>
            </td>
            <td style={{...td, fontWeight:600, color:"#fef3c7"}}>{ascendant.sign}</td>
            <td style={{...td, color:"rgba(254,243,199,0.45)"}}>{ascendant.sign_lord}</td>
            <td style={{...td, textAlign:"right", fontFamily:"monospace"}}>
              {ascendant.degree_in_sign?.toFixed(2)}°
            </td>
            <td style={{...td, textAlign:"center"}}>—</td>
            <td style={td}>{ascendant.nakshatra}</td>
            <td style={{...td, color:"rgba(254,243,199,0.45)"}}>{ascendant.nakshatra_lord}</td>
            <td style={{...td, textAlign:"center"}}>{ascendant.pada}</td>
            <td style={{...td, color:"rgba(254,243,199,0.45)"}}>—</td>
            <td style={{...td, textAlign:"center"}}>—</td>
          </tr>

          {PLANET_ORDER.map(planet => {
            const p  = planetPositions[planet]
            const d9 = navamsaPositions?.[planet]
            if (!p) return null
            const isRetro = p.retrograde
            const isVargo = d9?.vargottama
            return (
              <tr key={planet} style={{
                background: planetRowColor(planet),
                borderBottom:"1px solid rgba(251,191,36,0.1)",
              }}>
                <td style={td}>
                  <span style={{ marginRight:"6px", fontSize:"1rem" }}>
                    {PLANET_SYMBOLS[planet]}
                  </span>
                  <span style={{ fontWeight:600 }}>{planet}</span>
                  {isVargo && (
                    <span title="Vargottama" style={{
                      marginLeft:"4px", fontSize:"0.6rem",
                      color:"#f59e0b", fontWeight:700
                    }}>★V</span>
                  )}
                </td>
                <td style={{ ...td, fontWeight:500 }}>{p.sign}</td>
                <td style={{ ...td, color:"rgba(254,243,199,0.45)" }}>{p.sign_lord}</td>
                <td style={{ ...td, textAlign:"right", fontFamily:"monospace" }}>
                  {p.degree_in_sign?.toFixed(2)}°
                </td>
                <td style={{ ...td, textAlign:"center", fontWeight:600 }}>
                  H{p.house}
                </td>
                <td style={td}>{p.nakshatra}</td>
                <td style={{ ...td, color:"rgba(254,243,199,0.45)" }}>{p.nakshatra_lord}</td>
                <td style={{ ...td, textAlign:"center" }}>{p.pada}</td>
                <td style={{ ...td, color: isVargo ? "#f59e0b" : "#94a3b8" }}>
                  {d9?.sign || "—"}
                </td>
                <td style={{ ...td, textAlign:"center", color: isRetro ? "#f87171" : "rgba(254,243,199,0.25)" }}>
                  {isRetro ? "℞" : "—"}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

const th = {
  padding: "8px 10px",
  fontWeight: 600,
  fontSize: "0.72rem",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  borderBottom: "1px solid rgba(251,191,36,0.2)",
  whiteSpace: "nowrap",
}

const td = {
  padding: "7px 10px",
  whiteSpace: "nowrap",
}
