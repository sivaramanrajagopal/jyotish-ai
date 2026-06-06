/**
 * PlanetTable.jsx — theme-aware planet details table
 */

const PLANET_ORDER = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]

const PLANET_SYMBOLS = {
  Sun:"☉", Moon:"☽", Mars:"♂", Mercury:"☿",
  Jupiter:"♃", Venus:"♀", Saturn:"♄", Rahu:"☊", Ketu:"☋",
}

const CRISIS_SET = new Set(["Mars","Rahu","Saturn","Ketu"])
const GROWTH_SET = new Set(["Jupiter","Venus"])

function planetRowColor(planet) {
  if (GROWTH_SET.has(planet)) return "var(--row-growth)"
  if (CRISIS_SET.has(planet)) return "var(--row-crisis)"
  if (planet === "Sun")  return "var(--row-sun)"
  if (planet === "Moon") return "var(--row-moon)"
  return "var(--card-bg)"
}

const th = {
  padding: "8px 10px",
  fontWeight: 700,
  fontSize: "0.72rem",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  borderBottom: "2px solid var(--orange)",
  whiteSpace: "nowrap",
  color: "var(--text-secondary)",
  background: "var(--table-header)",
}

const td = {
  padding: "7px 10px",
  whiteSpace: "nowrap",
  color: "var(--text-primary)",
}

export default function PlanetTable({ planetPositions, navamsaPositions, ascendant }) {
  return (
    <div style={{ overflowX:"auto", WebkitOverflowScrolling:"touch" }}>
      <table style={{
        width:"100%",
        minWidth: "640px",
        borderCollapse:"collapse",
        fontFamily:"'Inter',system-ui,sans-serif",
        fontSize:"0.78rem",
      }}>
        <thead>
          <tr>
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
          <tr style={{ background:"var(--highlight-bg)", borderBottom:"2px solid var(--orange)" }}>
            <td style={td}>
              <span style={{ fontWeight:700, color:"var(--orange)" }}>⬆ Ascendant</span>
            </td>
            <td style={{...td, fontWeight:700, color:"var(--text-primary)"}}>{ascendant.sign}</td>
            <td style={{...td, color:"var(--text-muted)"}}>{ascendant.sign_lord}</td>
            <td style={{...td, textAlign:"right", fontFamily:"monospace", color:"var(--text-secondary)"}}>
              {ascendant.degree_in_sign?.toFixed(2)}°
            </td>
            <td style={{...td, textAlign:"center", color:"var(--text-muted)"}}>—</td>
            <td style={{...td, color:"var(--text-secondary)"}}>{ascendant.nakshatra}</td>
            <td style={{...td, color:"var(--text-muted)"}}>{ascendant.nakshatra_lord}</td>
            <td style={{...td, textAlign:"center", color:"var(--text-secondary)"}}>{ascendant.pada}</td>
            <td style={{...td, color:"var(--text-muted)"}}>—</td>
            <td style={{...td, textAlign:"center", color:"var(--text-muted)"}}>—</td>
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
                borderBottom:"1px solid var(--card-border)",
              }}>
                <td style={td}>
                  <span style={{ marginRight:"6px", fontSize:"1rem" }}>
                    {PLANET_SYMBOLS[planet]}
                  </span>
                  <span style={{ fontWeight:600, color:"var(--text-primary)" }}>{planet}</span>
                  {isVargo && (
                    <span title="Vargottama" style={{
                      marginLeft:"4px", fontSize:"0.6rem",
                      color:"var(--orange-dark)", fontWeight:700
                    }}>★V</span>
                  )}
                </td>
                <td style={{ ...td, fontWeight:600, color:"var(--text-primary)" }}>{p.sign}</td>
                <td style={{ ...td, color:"var(--text-muted)" }}>{p.sign_lord}</td>
                <td style={{ ...td, textAlign:"right", fontFamily:"monospace", color:"var(--text-secondary)" }}>
                  {p.degree_in_sign?.toFixed(2)}°
                </td>
                <td style={{ ...td, textAlign:"center", fontWeight:700, color:"var(--orange)" }}>
                  H{p.house}
                </td>
                <td style={{...td, color:"var(--text-secondary)"}}>{p.nakshatra}</td>
                <td style={{ ...td, color:"var(--text-muted)" }}>{p.nakshatra_lord}</td>
                <td style={{ ...td, textAlign:"center", color:"var(--text-secondary)" }}>{p.pada}</td>
                <td style={{ ...td, color: isVargo ? "var(--orange-dark)" : "var(--text-muted)" }}>
                  {d9?.sign || "—"}
                </td>
                <td style={{ ...td, textAlign:"center", color: isRetro ? "var(--error-text)" : "var(--text-muted)", fontWeight: isRetro ? 700 : 400 }}>
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
