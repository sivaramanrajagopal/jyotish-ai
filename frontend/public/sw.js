/* Parashara Jyotish — service worker for cosmic alert notifications */

const ALLOWED_TABS = new Set(['home', 'chart', 'panchangam', 'chat', 'forecast'])

function safeInternalPath(raw) {
  try {
    const u = new URL(raw || '/', self.location.origin)
    if (u.origin !== self.location.origin) return '/'
    const tab = u.searchParams.get('tab')
    if (tab && !ALLOWED_TABS.has(tab)) {
      u.searchParams.delete('tab')
    }
    return u.pathname + u.search
  } catch {
    return '/'
  }
}

self.addEventListener('install', () => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const path = safeInternalPath(event.notification.data?.url)
  const fullUrl = new URL(path, self.location.origin).href

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ('focus' in client) {
          const tab = new URL(path, self.location.origin).searchParams.get('tab')
          if (tab && ALLOWED_TABS.has(tab)) {
            client.postMessage({ type: 'NAV_TAB', tab })
          }
          return client.focus()
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(fullUrl)
    })
  )
})

self.addEventListener('message', (event) => {
  if (event.origin && event.origin !== self.location.origin) return
  const { type, title, body, tag, url } = event.data || {}
  if (type !== 'SHOW_NOTIFICATION') return
  const safeUrl = safeInternalPath(url)
  event.waitUntil(
    self.registration.showNotification(title || 'Parashara Jyotish', {
      body: body || '',
      icon: '/icons/icon-192.svg',
      badge: '/icons/icon-192.svg',
      tag: tag || 'jyotish-alert',
      data: { url: safeUrl },
    })
  )
})
