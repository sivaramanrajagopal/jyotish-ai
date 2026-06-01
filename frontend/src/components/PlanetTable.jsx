/**
 * PlanetTable.jsx — light Amazon theme
 */

const PLANET_ORDER = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]

const PLANET_SYMBOLS = {
  Sun:"☉", Moon:"☽", Mars:"♂", Mercury:"☿",
  Jupiter:"♃", Venus:"♀", Saturn:"♄", Rahu:"☊", Ketu:"☋",
}

const CRISIS_SET = new Set(["Mars","Rahu","Saturn","Ketu"])
const GROWTH_SET = new Set(["Jupiter","Venus"])

function planetRowColor(planet) {
  if (GROWTH_SET.has(planet)) return "#F0FFF4"
  if (CRISIS_SET.has(planet)) return "#FFF8F8"
  if (planet === "Sun")  return "#FFFBF0"
  if (planet === "Moon") return "#F0F8FF"
  return "#FFFFFF"
}

const th = {
  padding: "8px 10px",
  fontWeight: 700,
  fontSize: "0.72rem",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  borderBottom: "2px solid #FF9900",
  whiteSpace: "nowrap",
  color: "#444",
  background: "#FFF8F0",
}

const td = {
  padding: "7px 10px",
  whiteSpace: "nowrap",
  color: "#1A1A1A",
}

export default function PlanetTable({ planetPositions, navamsaPositions, ascendant }) {
  return (
    <div style={{ overflowX:"auto" }}>
      <table style={{
        width:"100%",
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
          {/* Ascendant row */}
          <tr style={{ background:"#FFF8F0", borderBottom:"2px solid #FF9900" }}>
            <td style={td}>
              <span style={{ fontWeight:700, color:"#FF9900" }}>⬆ Ascendant</span>
            </td>
            <td style={{...td, fontWeight:700, color:"#232F3E"}}>{ascendant.sign}</td>
            <td style={{...td, color:"#888"}}>{ascendant.sign_lord}</td>
            <td style={{...td, textAlign:"right", fontFamily:"monospace", color:"#555"}}>
              {ascendant.degree_in_sign?.toFixed(2)}°
            </td>
            <td style={{...td, textAlign:"center", color:"#888"}}>—</td>
            <td style={{...td, color:"#444"}}>{ascendant.nakshatra}</td>
            <td style={{...td, color:"#888"}}>{ascendant.nakshatra_lord}</td>
            <td style={{...td, textAlign:"center", color:"#555"}}>{ascendant.pada}</td>
            <td style={{...td, color:"#888"}}>—</td>
            <td style={{...td, textAlign:"center", color:"#888"}}>—</td>
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
                borderBottom:"1px solid #EEE",
              }}>
                <td style={td}>
                  <span style={{ marginRight:"6px", fontSize:"1rem" }}>
                    {PLANET_SYMBOLS[planet]}
                  </span>
                  <span style={{ fontWeight:600, color:"#232F3E" }}>{planet}</span>
                  {isVargo && (
                    <span title="Vargottama" style={{
                      marginLeft:"4px", fontSize:"0.6rem",
                      color:"#E47911", fontWeight:700
                    }}>★V</span>
                  )}
                </td>
                <td style={{ ...td, fontWeight:600, color:"#232F3E" }}>{p.sign}</td>
                <td style={{ ...td, color:"#888" }}>{p.sign_lord}</td>
                <td style={{ ...td, textAlign:"right", fontFamily:"monospace", color:"#555" }}>
                  {p.degree_in_sign?.toFixed(2)}°
                </td>
                <td style={{ ...td, textAlign:"center", fontWeight:700, color:"#FF9900" }}>
                  H{p.house}
                </td>
                <td style={{...td, color:"#444"}}>{p.nakshatra}</td>
                <td style={{ ...td, color:"#888" }}>{p.nakshatra_lord}</td>
                <td style={{ ...td, textAlign:"center", color:"#555" }}>{p.pada}</td>
                <td style={{ ...td, color: isVargo ? "#E47911" : "#888" }}>
                  {d9?.sign || "—"}
                </td>
                <td style={{ ...td, textAlign:"center", color: isRetro ? "#D13212" : "#CCC", fontWeight: isRetro ? 700 : 400 }}>
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
