/**
 * Open the expert tab that produced the numbers. Same look as the existing chips.
 */
export default function CiteChips({ cites, onGoToTab }) {
  if (!cites?.length || !onGoToTab) return null
  return (
    <div className="flex flex-wrap gap-2 mt-2" aria-label="Open the matching tab">
      {cites.map((cite) => (
        <button
          key={cite.tab}
          type="button"
          onClick={() => onGoToTab(cite.tab)}
          className="text-xs font-semibold px-3 py-2 rounded-full min-h-[44px]"
          style={{
            background: 'var(--chip-bg)',
            border: '1px solid var(--chip-border)',
            color: 'var(--text-secondary)',
          }}
        >
          Show on {cite.label}
        </button>
      ))}
    </div>
  )
}
