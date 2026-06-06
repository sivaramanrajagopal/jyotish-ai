/**
 * LanguageToggle.jsx
 * Pill-style EN | தமிழ் toggle button.
 */
export default function LanguageToggle({ language, onChange }) {
  return (
    <div
      style={{
        display: 'inline-flex',
        background: 'var(--toggle-bg)',
        borderRadius: 20,
        padding: 3,
        gap: 2,
        userSelect: 'none',
        border: '1px solid var(--chip-border)',
      }}
      title="Switch response language"
    >
      {[
        { key: 'english', label: 'EN' },
        { key: 'tamil',   label: 'தமிழ்' },
      ].map(({ key, label }) => {
        const active = language === key
        return (
          <button
            key={key}
            onClick={() => onChange(key)}
            style={{
              padding:      '4px 12px',
              borderRadius: 16,
              border:       'none',
              cursor:       'pointer',
              fontSize:     key === 'tamil' ? 12 : 11,
              fontWeight:   700,
              background:   active ? 'var(--orange)' : 'transparent',
              color:        active ? 'var(--accent-dark)' : 'var(--text-muted)',
              transition:   'all 0.15s',
              lineHeight:   1.4,
            }}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}
