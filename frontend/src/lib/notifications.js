/**
 * Cosmic alerts — Chandra Ashtama, Rahu Kalam, Tara Balam warnings.
 * Uses Service Worker + Notification API when permitted.
 */

import api from '../api/client'

const PREFS_KEY = 'jyotish-notif-prefs-v1'
const SENT_KEY  = 'jyotish-notif-sent-v1'
const CHECK_MS  = 5 * 60 * 1000  // every 5 minutes while app is open

const DEFAULT_PREFS = {
  enabled: false,
  chandraAshtama: true,
  rahuKalam: true,
  taraWarnings: true,
  location: 'Chennai',
}

export function getNotificationPrefs() {
  try {
    const raw = localStorage.getItem(PREFS_KEY)
    return raw ? { ...DEFAULT_PREFS, ...JSON.parse(raw) } : { ...DEFAULT_PREFS }
  } catch {
    return { ...DEFAULT_PREFS }
  }
}

export function saveNotificationPrefs(prefs) {
  try {
    localStorage.setItem(PREFS_KEY, JSON.stringify({ ...DEFAULT_PREFS, ...prefs }))
  } catch {}
}

function todayKey() {
  return new Date().toISOString().split('T')[0]
}

function getSentLog() {
  try {
    const raw = localStorage.getItem(SENT_KEY)
    const log = raw ? JSON.parse(raw) : {}
    const today = todayKey()
    if (log._date !== today) return { _date: today }
    return log
  } catch {
    return { _date: todayKey() }
  }
}

function markSent(tag) {
  const log = getSentLog()
  log[tag] = true
  log._date = todayKey()
  try { localStorage.setItem(SENT_KEY, JSON.stringify(log)) } catch {}
}

function alreadySent(tag) {
  const log = getSentLog()
  return log._date === todayKey() && !!log[tag]
}

export async function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return null
  try {
    return await navigator.serviceWorker.register('/sw.js', { scope: '/' })
  } catch (e) {
    console.warn('[notifications] SW registration failed', e)
    return null
  }
}

export async function requestNotificationPermission() {
  if (!('Notification' in window)) {
    return { granted: false, reason: 'Notifications not supported in this browser.' }
  }
  if (Notification.permission === 'granted') return { granted: true }
  if (Notification.permission === 'denied') {
    return { granted: false, reason: 'Notifications blocked. Enable them in browser settings.' }
  }
  const result = await Notification.requestPermission()
  return { granted: result === 'granted', reason: result !== 'granted' ? 'Permission denied.' : null }
}

async function showNotification(title, body, tag, url = '/') {
  if (Notification.permission !== 'granted') return
  if (alreadySent(tag)) return

  const reg = await navigator.serviceWorker?.ready?.catch(() => null)
  if (reg?.active) {
    reg.active.postMessage({ type: 'SHOW_NOTIFICATION', title, body, tag, url })
  } else if ('Notification' in window) {
    new Notification(title, {
      body,
      icon: '/icons/icon-192.svg',
      tag,
      data: { url },
    })
  }
  markSent(tag)
}

function guessLocation(place) {
  if (!place) return 'Chennai'
  const cities = ['Chennai', 'Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Coimbatore', 'Erlangen']
  const lower = place.toLowerCase()
  return cities.find(c => lower.includes(c.toLowerCase())) || 'Chennai'
}

function fmtTime(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit', hour12: true, timeZone: 'Asia/Kolkata',
    })
  } catch { return '' }
}

function isNow(startIso, endIso) {
  if (!startIso || !endIso) return false
  const now = Date.now()
  return now >= new Date(startIso).getTime() && now <= new Date(endIso).getTime()
}

function minutesUntil(iso) {
  if (!iso) return Infinity
  return (new Date(iso).getTime() - Date.now()) / 60000
}

/** Run all alert checks for a saved natal chart */
export async function checkCosmicAlerts(chart, placeOfBirth) {
  const prefs = getNotificationPrefs()
  if (!prefs.enabled || Notification.permission !== 'granted') return
  if (chart?.moon_nakshatra_index == null || chart?.moon_rasi_index == null) return

  const location = prefs.location || guessLocation(placeOfBirth)
  const nakIdx   = chart.moon_nakshatra_index
  const rasiIdx  = chart.moon_rasi_index

  try {
    if (prefs.chandraAshtama || prefs.taraWarnings) {
      const { data } = await api.get('/personal-panchangam/anonymous', {
        params: { natal_nak_index: nakIdx, natal_rasi_index: rasiIdx, timezone: 'Asia/Kolkata' },
      })

      if (prefs.chandraAshtama && data?.chandra_ashtama?.is_active && !alreadySent('ashtama-active')) {
        await showNotification(
          '🛡️ Chandra Ashtama Active',
          `Moon in your 8th sign (${data.chandra_ashtama.ashtama_rasi_name || ''}). Avoid major decisions today.`,
          'ashtama-active',
          '/?tab=chart'
        )
      }

      const tara = data?.tara
      if (prefs.taraWarnings && tara?.colour === 'red' && !alreadySent('tara-bad')) {
        await showNotification(
          '⭐ Tara Balam — Caution',
          `${tara.name} (${tara.nature}): ${tara.meaning || 'Unfavourable day for new beginnings.'}`,
          'tara-bad',
          '/?tab=chart'
        )
      }
    }

    if (prefs.rahuKalam) {
      const { data: panch } = await api.get('/panchangam/today', { params: { location } })
      const rahuStart = panch?.rahu_kalam_start
      const rahuEnd   = panch?.rahu_kalam_end

      if (isNow(rahuStart, rahuEnd) && !alreadySent('rahu-active')) {
        await showNotification(
          '🔴 Rahu Kalam — Now',
          `Inauspicious window until ${fmtTime(rahuEnd)}. Postpone new starts if possible.`,
          'rahu-active',
          '/?tab=panchangam'
        )
      } else {
        const mins = minutesUntil(rahuStart)
        if (mins > 0 && mins <= 10 && !alreadySent('rahu-soon')) {
          await showNotification(
            '⏳ Rahu Kalam Starting Soon',
            `Begins at ${fmtTime(rahuStart)} (~${Math.round(mins)} min). Plan important work outside this window.`,
            'rahu-soon',
            '/?tab=panchangam'
          )
        }
      }
    }
  } catch (e) {
    console.warn('[notifications] check failed', e)
  }
}

/** Start periodic checks while the app is open */
export function startNotificationWatcher(chart, placeOfBirth) {
  if (!chart) return () => {}

  registerServiceWorker()
  checkCosmicAlerts(chart, placeOfBirth)

  const id = setInterval(() => {
    if (document.visibilityState === 'visible') {
      checkCosmicAlerts(chart, placeOfBirth)
    }
  }, CHECK_MS)

  const onVisible = () => {
    if (document.visibilityState === 'visible') checkCosmicAlerts(chart, placeOfBirth)
  }
  document.addEventListener('visibilitychange', onVisible)

  return () => {
    clearInterval(id)
    document.removeEventListener('visibilitychange', onVisible)
  }
}
