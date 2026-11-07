/**
 * Theme helpers: data-theme on <html>, persisted to localStorage.
 */
export const THEME_KEY = 'jyotish-theme'

export function getInitialTheme() {
  try {
    const stored = localStorage.getItem(THEME_KEY)
    if (stored === 'dark' || stored === 'light') return stored
  } catch {
    // Storage blocked (private mode); fall back to the system preference.
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme)
  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) meta.setAttribute('content', theme === 'dark' ? '#0F1111' : '#FF9900')
  document.documentElement.style.background = theme === 'dark' ? '#0F1111' : '#FFF8F0'
}

export function saveTheme(theme) {
  try {
    localStorage.setItem(THEME_KEY, theme)
  } catch {
    // Storage blocked; the theme still applies for this visit.
  }
}

/** Call this once at app startup to apply the persisted theme immediately */
export function applyStoredTheme() {
  applyTheme(getInitialTheme())
}
