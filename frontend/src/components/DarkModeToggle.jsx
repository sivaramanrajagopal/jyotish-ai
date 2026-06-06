/**
 * DarkModeToggle.jsx
 * Reads/writes data-theme on <html> and persists to localStorage.
 */
import { useState, useEffect } from 'react'

function getInitialTheme() {
  try {
    const stored = localStorage.getItem('jyotish-theme')
    if (stored === 'dark' || stored === 'light') return stored
  } catch {}
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme)
  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) meta.setAttribute('content', theme === 'dark' ? '#0F1111' : '#FF9900')
  document.documentElement.style.background = theme === 'dark' ? '#0F1111' : '#FFF8F0'
}

export default function DarkModeToggle({ small = false, onDarkBg = true }) {
  const [theme, setTheme] = useState(getInitialTheme)

  useEffect(() => {
    applyTheme(theme)
    try { localStorage.setItem('jyotish-theme', theme) } catch {}
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

/** Call this once at app startup to apply the persisted theme immediately */
export function applyStoredTheme() {
  try {
    const stored = localStorage.getItem('jyotish-theme')
    if (stored === 'dark' || stored === 'light') {
      applyTheme(stored)
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      applyTheme('dark')
    } else {
      applyTheme('light')
    }
  } catch {}
}
