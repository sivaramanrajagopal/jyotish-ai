/**
 * Persist chat messages for the current chart session (sessionStorage, 24h TTL).
 */
import { chartFingerprint } from './chartPayload'

const PREFIX = 'jyotish-chat-'
const TTL_MS = 24 * 60 * 60 * 1000

function storageKey(chart) {
  const fp = chartFingerprint(chart)
  return `${PREFIX}${fp || 'default'}`
}

export function loadChatMessages(chart) {
  try {
    const raw = sessionStorage.getItem(storageKey(chart))
    if (!raw) return []
    const parsed = JSON.parse(raw)
    const age = Date.now() - new Date(parsed.savedAt).getTime()
    if (age > TTL_MS) {
      sessionStorage.removeItem(storageKey(chart))
      return []
    }
    return Array.isArray(parsed.messages) ? parsed.messages : []
  } catch {
    return []
  }
}

export function saveChatMessages(chart, messages) {
  try {
    sessionStorage.setItem(storageKey(chart), JSON.stringify({
      messages,
      savedAt: new Date().toISOString(),
    }))
  } catch {}
}

export function clearChatMessages(chart) {
  try { sessionStorage.removeItem(storageKey(chart)) } catch {}
}
