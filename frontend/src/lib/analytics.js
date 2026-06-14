/**
 * Product analytics — optional GA4 + server-side app_events (via POST /analytics/event).
 * Best-effort only; never blocks the UI.
 */

import api from '../api/client'

const GA_ID = import.meta.env.VITE_GA_MEASUREMENT_ID?.trim()

/** Stop POST spam if backend hasn't deployed /analytics/event yet (404). */
let backendEventsEnabled = true

function loadGtag() {
  window.dataLayer = window.dataLayer || []
  window.gtag = function gtag() { window.dataLayer.push(arguments) }
  const script = document.createElement('script')
  script.async = true
  script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(GA_ID)}`
  document.head.appendChild(script)
  window.gtag('js', new Date())
  window.gtag('config', GA_ID, { send_page_view: false })
}

export function initAnalytics() {
  if (!GA_ID || typeof window === 'undefined' || window.__gaInitialized) return
  window.__gaInitialized = true
  loadGtag()
}

export function trackEvent(eventName, properties = {}) {
  if (!eventName || typeof eventName !== 'string') return

  if (GA_ID && window.gtag) {
    window.gtag('event', eventName, properties)
  }

  if (!backendEventsEnabled) return

  api.post('/analytics/event', {
    event_name: eventName,
    properties,
  }).catch((err) => {
    if (err.response?.status === 404) {
      backendEventsEnabled = false
    }
  })
}

export function trackTabView(tab) {
  trackEvent('tab_view', { tab })
}
