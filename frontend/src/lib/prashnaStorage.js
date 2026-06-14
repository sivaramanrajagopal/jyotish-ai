const STORAGE_KEY = 'jyotish-prashna-history'
const MAX_ITEMS = 20

export function loadPrashnaHistory() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function savePrashnaSession(entry) {
  try {
    const list = loadPrashnaHistory()
    list.unshift({
      ...entry,
      saved_at: new Date().toISOString(),
    })
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX_ITEMS)))
  } catch {
    /* ignore quota errors */
  }
}

export function clearPrashnaHistory() {
  try {
    sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    /* ignore */
  }
}
