/**
 * Chart persistence — session-only for anonymous users (Step 6).
 * Signed-in users load/save via GET/POST /natal-chart on the server.
 */

const SESSION_KEY = 'jyotish-chart-session'
const LEGACY_KEY = 'jyotish-chart-v1'
const TTL_MS = 24 * 60 * 60 * 1000 // sessionStorage: 24h

export function saveSessionChart(form, chart) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({
      form, chart, savedAt: new Date().toISOString(),
    }))
  } catch {}
}

export function loadSessionChart() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY)
    if (!raw) return migrateLegacyLocalStorage()
    const parsed = JSON.parse(raw)
    const age = Date.now() - new Date(parsed.savedAt).getTime()
    if (age > TTL_MS) {
      sessionStorage.removeItem(SESSION_KEY)
      return null
    }
    return parsed
  } catch {
    return null
  }
}

/** One-time migration from old localStorage key; then remove PII from localStorage. */
function migrateLegacyLocalStorage() {
  try {
    const raw = localStorage.getItem(LEGACY_KEY)
    if (!raw) return null
    localStorage.removeItem(LEGACY_KEY)
    const parsed = JSON.parse(raw)
    saveSessionChart(parsed.form, parsed.chart)
    return parsed
  } catch {
    try { localStorage.removeItem(LEGACY_KEY) } catch {}
    return null
  }
}

export function clearSessionChart() {
  try { sessionStorage.removeItem(SESSION_KEY) } catch {}
  try { localStorage.removeItem(LEGACY_KEY) } catch {}
}
