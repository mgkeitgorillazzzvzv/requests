/// <reference lib="webworker" />
const sw = self;

const CACHE_NAME = 'mgkeit-requests-v2';
const urlsToCache = [
  '/',
  '/manifest.json',
  '/icons/16.png',
  '/icons/20.png',
  '/icons/29.png',
  '/icons/32.png',
  '/icons/40.png',
  '/icons/50.png',
  '/icons/57.png',
  '/icons/58.png',
  '/icons/60.png',
  '/icons/64.png',
  '/icons/72.png',
  '/icons/76.png',
  '/icons/80.png',
  '/icons/87.png',
  '/icons/100.png',
  '/icons/114.png',
  '/icons/120.png',
  '/icons/128.png',
  '/icons/144.png',
  '/icons/152.png',
  '/icons/167.png',
  '/icons/180.png',
  '/icons/192.png',
  '/icons/256.png',
  '/icons/512.png',
  '/icons/1024.png'
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
