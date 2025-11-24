/// <reference lib="webworker" />
const sw = self;

const CACHE_NAME = 'mgkeit-requests-v1';
const urlsToCache = [
  '/',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];


sw.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
      .then(() => sw.skipWaiting())
  );
});


sw.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => sw.clients.claim())
  );
});


sw.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        
        if (response) {
          return response;
        }

        
        const fetchRequest = event.request.clone();

        return fetch(fetchRequest).then((response) => {
          
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          
          const responseToCache = response.clone();

          
          if (!event.request.url.includes('/api/')) {
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });
          }

          return response;
        }).catch(() => {
          
          return caches.match('/');
        });
      })
  );
});


sw.addEventListener('push', (event) => {
  const data = event.data?.json() ?? {};
  
  const title = data.title || 'Новое уведомление';
  const options = {
    body: data.body || '',
    icon: data.icon || '/icons/icon-192x192.png',
    badge: data.badge || '/icons/icon-192x192.png',
    vibrate: [200, 100, 200],
    data: data.data || {},
    actions: [
      {
        action: 'open',
        title: 'Открыть'
      },
      {
        action: 'close',
        title: 'Закрыть'
      }
    ],
    requireInteraction: true,
    tag: 'mgkeit-request'
  };

  event.waitUntil(
    sw.registration.showNotification(title, options)
  );
});


sw.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'close') {
    return;
  }

  
  event.waitUntil(
    sw.clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        const url = event.notification.data?.url || '/';
        
        
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            return client.focus().then(() => {
              if ('navigate' in client) {
                return client.navigate(url);
              }
            });
          }
        }
        
        
        if (sw.clients.openWindow) {
          return sw.clients.openWindow(url);
        }
      })
  );
});


sw.addEventListener('sync', (event) => {
  if (event.tag === 'sync-requests') {
    event.waitUntil(
      
      Promise.resolve()
    );
  }
});
