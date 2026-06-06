/**
 * LanguageToggle.jsx
 * Pill-style EN | தமிழ் toggle button.
 * Usage: <LanguageToggle language={lang} onChange={setLang} />
 */
export default function LanguageToggle({ language, onChange }) {
  const isEn = language !== 'tamil'
  return (
    <div
      style={{
        display: 'inline-flex',
        background: '#F0F0F0',
        borderRadius: 20,
        padding: 3,
        gap: 2,
        userSelect: 'none',
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
              background:   active ? '#FF9900' : 'transparent',
              color:        active ? '#232F3E' : '#888',
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
