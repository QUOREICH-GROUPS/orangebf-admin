self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('orange-admin-cache-v1').then((cache) => cache.add('/'))
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') {
    return;
  }
  event.respondWith(
    caches.match(request).then((cached) => cached || fetch(request))
  );
});
