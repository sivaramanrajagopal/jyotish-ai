/* Jyotish AI — service worker for cosmic alert notifications */

self.addEventListener('install', () => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const path = event.notification.data?.url || '/'
  const fullUrl = new URL(path, self.location.origin).href

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ('focus' in client) {
          const tab = new URL(path, self.location.origin).searchParams.get('tab')
          if (tab) client.postMessage({ type: 'NAV_TAB', tab })
          return client.focus()
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(fullUrl)
    })
  )
})

self.addEventListener('message', (event) => {
  const { type, title, body, tag, url } = event.data || {}
  if (type !== 'SHOW_NOTIFICATION') return
  event.waitUntil(
    self.registration.showNotification(title || 'Jyotish AI', {
      body: body || '',
      icon: '/icons/icon-192.svg',
      badge: '/icons/icon-192.svg',
      tag: tag || 'jyotish-alert',
      data: { url: url || '/' },
    })
  )
})
