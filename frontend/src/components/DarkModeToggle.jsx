/**
 * DarkModeToggle.jsx
 * Reads/writes data-theme on <html> and persists to localStorage.
 */
import { useState, useEffect } from 'react'
import { applyTheme, getInitialTheme, saveTheme } from '../lib/theme'

export default function DarkModeToggle({ small = false, onDarkBg = true }) {
  const [theme, setTheme] = useState(getInitialTheme)

  useEffect(() => {
    applyTheme(theme)
    saveTheme(theme)
  }, [theme])

  const toggle = () => setTheme(t => t === 'dark' ? 'light' : 'dark')
  const isDark  = theme === 'dark'

  return (
    <button
      onClick={toggle}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      style={{
        background:   onDarkBg ? 'transparent' : 'var(--chip-bg)',
        border:       onDarkBg ? '1px solid rgba(255,255,255,0.2)' : '1px solid var(--chip-border)',
        borderRadius: 20,
        padding:      small ? '3px 8px' : '4px 10px',
        cursor:       'pointer',
        fontSize:     small ? 13 : 15,
        lineHeight:   1,
        color:        'var(--orange)',
        display:      'flex',
        alignItems:   'center',
        gap:          4,
        flexShrink:   0,
      }}
    >
      {isDark ? '☀️' : '🌙'}
      {!small && (
        <span style={{
          fontSize: 10,
          fontWeight: 600,
          color: onDarkBg ? 'rgba(255,255,255,0.6)' : 'var(--text-muted)',
        }}>
          {isDark ? 'LIGHT' : 'DARK'}
        </span>
      )}
    </button>
  )
}