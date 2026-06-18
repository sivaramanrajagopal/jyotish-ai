/* Parashara Jyotish — service worker: offline shell + cosmic alert notifications */

const CACHE_SHELL = 'jyotish-shell-v3'
const SHELL_URLS = ['/', '/index.html', '/manifest.json', '/icons/icon-192.svg', '/icons/icon-512.svg']

const ALLOWED_TABS = new Set([
  'home', 'chart', 'career', 'health', 'dosha-radar', 'gochar',
  'panchangam', 'chat', 'forecast', 'prashna', 'admin',
])

function offlineHtmlResponse() {
  return new Response(
    '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Offline</title></head>'
    + '<body><p>Parashara Jyotish is offline. Check your connection and reload.</p></body></html>',
    { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } },
  )
}

async function cachedShellResponse() {
  const cached = await caches.match('/index.html') || await caches.match('/')
  return cached || offlineHtmlResponse()
}

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

function isNavigationRequest(request) {
  return request.mode === 'navigate'
    || (request.method === 'GET' && request.headers.get('accept')?.includes('text/html'))
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_SHELL)
      .then((cache) => cache.addAll(SHELL_URLS))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k.startsWith('jyotish-shell-') && k !== CACHE_SHELL).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return

  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return
  if (url.pathname.startsWith('/api')) return
  if (url.pathname.startsWith('/auth')) return

  if (isNavigationRequest(request)) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.ok) {
            const copy = response.clone()
            caches.open(CACHE_SHELL).then((cache) => cache.put('/index.html', copy))
          }
          return response
        })
        .catch(() => cachedShellResponse()),
    )
    return
  }

  event.respondWith(
    fetch(request)
      .then((response) => response)
      .catch(() => caches.match(request).then((r) => r || offlineHtmlResponse())),
  )
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
