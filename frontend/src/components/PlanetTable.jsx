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

function PushkaraMark({ seat }) {
  if (!seat?.mark) return null
  const degree = seat.mark === 'degree'
  const label = degree ? 'Pushkara degree' : 'Pushkara'
  const title = degree
    ? `Within 1° of the Pushkara degree, ${seat.sign} ${seat.bhaga}°`
    : `Pushkara Navamsa, ${seat.nakshatra} pada ${seat.pada}`
  return (
    <div title={title} style={{
      marginTop: 2,
      fontSize: '0.62rem',
      fontWeight: 700,
      letterSpacing: '0.02em',
      color: degree ? 'var(--orange-dark)' : 'var(--text-secondary)',
      whiteSpace: 'normal',
    }}>
      {label}
    </div>
  )
}

function MobileRow({ name, sign, degree, house, nakshatra, pada, d9, retro, seat, vargottama }) {
  return (
    <li
      className="rounded-md px-2.5 py-2 text-sm"
      style={{
        color: 'var(--text-primary)',
        background: 'var(--surface-muted)',
        border: '1px solid var(--card-border)',
        overflowWrap: 'anywhere',
      }}
    >
      <p className="font-semibold">
        {name}
        {retro ? ' · retrograde' : ''}
        {vargottama ? ' · vargottama' : ''}
      </p>
      <p>
        {sign} {degree?.toFixed(2)}° · house {house}
      </p>
      <p style={{ color: 'var(--text-muted)' }}>
        {nakshatra} pada {pada}
        {d9 ? ` · Navamsa ${d9}` : ''}
      </p>
      <PushkaraMark seat={seat} />
    </li>
  )
}

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

export default function PlanetTable({ planetPositions, navamsaPositions, ascendant, navamsaAscendant }) {
  const d9Lagna = navamsaAscendant?.sign
  const lagnaVargottama = Boolean(d9Lagna && d9Lagna === ascendant?.sign)
  const rows = PLANET_ORDER.map((planet) => {
    const p = planetPositions[planet]
    if (!p) return null
    return { planet, p, d9: navamsaPositions?.[planet] }
  }).filter(Boolean)

  return (
    <>
      <ul className="md:hidden space-y-2 p-3" aria-label="Planet degrees and Pushkara marks">
        <MobileRow
          name="Ascendant"
          sign={ascendant.sign}
          degree={ascendant.degree_in_sign}
          house={1}
          nakshatra={ascendant.nakshatra}
          pada={ascendant.pada}
          d9={d9Lagna}
          seat={ascendant.pushkara}
          vargottama={lagnaVargottama}
        />
        {rows.map(({ planet, p, d9 }) => (
          <MobileRow
            key={planet}
            name={planet}
            sign={p.sign}
            degree={p.degree_in_sign}
            house={p.house}
            nakshatra={p.nakshatra}
            pada={p.pada}
            d9={d9?.sign}
            retro={p.retrograde}
            seat={p.pushkara}
            vargottama={d9?.vargottama}
          />
        ))}
      </ul>
    <div className="hidden md:block" style={{ overflowX:"auto", WebkitOverflowScrolling:"touch" }}>
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
            <td style={{...td, textAlign:"right", fontFamily:"monospace", color:"var(--text-secondary)", whiteSpace:"normal"}}>
              {ascendant.degree_in_sign?.toFixed(2)}°
              <PushkaraMark seat={ascendant.pushkara} />
            </td>
            <td style={{...td, textAlign:"center", fontWeight:700, color:"var(--orange)"}}>H1</td>
            <td style={{...td, color:"var(--text-secondary)"}}>{ascendant.nakshatra}</td>
            <td style={{...td, color:"var(--text-muted)"}}>{ascendant.nakshatra_lord}</td>
            <td style={{...td, textAlign:"center", color:"var(--text-secondary)"}}>{ascendant.pada}</td>
            <td style={{
              ...td,
              fontWeight: 600,
              color: lagnaVargottama ? "var(--orange-dark)" : "var(--text-primary)",
            }}
              title={lagnaVargottama ? "Vargottama lagna" : "Navamsa lagna sign"}
            >
              {d9Lagna || "—"}
              {lagnaVargottama && (
                <span title="Vargottama" style={{
                  marginLeft: "4px", fontSize: "0.6rem",
                  color: "var(--orange-dark)", fontWeight: 700,
                }}>★V</span>
              )}
            </td>
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
                <td style={{ ...td, textAlign:"right", fontFamily:"monospace", color:"var(--text-secondary)", whiteSpace:"normal" }}>
                  {p.degree_in_sign?.toFixed(2)}°
                  <PushkaraMark seat={p.pushkara} />
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
    </>
  )
}
