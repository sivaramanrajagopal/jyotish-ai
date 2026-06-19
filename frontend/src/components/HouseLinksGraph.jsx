/**
 * HouseLinksGraph — 12-house SVG prediction map.
 */
export default function HouseLinksGraph({ graph, focusHouse, onSelectHouse }) {
  if (!graph?.nodes?.length) return null

  const edges = graph.edges || []
  const maxWeight = Math.max(1, ...edges.map(e => e.weight || 1))

  const visibleEdges = focusHouse
    ? edges.filter(e => e.from === focusHouse || e.to === focusHouse)
    : edges.filter(e => e.weight >= 3).slice(0, 24)

  return (
    <svg
      viewBox="0 0 100 100"
      className="hl-graph"
      role="img"
      aria-label="House connection graph"
    >
      {visibleEdges.map(e => {
        const from = graph.nodes.find(n => n.id === e.from)
        const to = graph.nodes.find(n => n.id === e.to)
        if (!from || !to) return null
        const supportive = e.supportive !== false
        return (
          <line
            key={e.id}
            x1={from.x}
            y1={from.y}
            x2={to.x}
            y2={to.y}
            className={`hl-graph__edge ${supportive ? 'hl-graph__edge--support' : 'hl-graph__edge--stress'}`}
            strokeWidth={0.3 + (e.weight / maxWeight) * 0.8}
            opacity={focusHouse ? 0.85 : 0.45}
          />
        )
      })}
      {graph.nodes.map(n => {
        const active = focusHouse === n.id
        const rag = n.rag || 'moderate'
        return (
          <g
            key={n.id}
            className={`hl-graph__node hl-graph__node--${rag} ${active ? 'hl-graph__node--active' : ''}`}
            onClick={() => onSelectHouse?.(n.id)}
            onKeyDown={ev => ev.key === 'Enter' && onSelectHouse?.(n.id)}
            role="button"
            tabIndex={0}
            aria-label={`House ${n.id} ${n.theme_en}`}
            style={{ cursor: 'pointer' }}
          >
            <circle cx={n.x} cy={n.y} r={active ? 5.5 : 4.2} />
            <text x={n.x} y={n.y + 0.5} textAnchor="middle" className="hl-graph__label">
              {n.house}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
