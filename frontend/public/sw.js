// Cache version - update this when deploying new code
const CACHE_VERSION = 'dev';
const CACHE_NAME = 'chesscrew-' + CACHE_VERSION;
const API_CACHE_NAME = 'chesscrew-api-cache-' + CACHE_VERSION;
const STATIC_ASSETS = [
  '/',
  '/static/js/main.js',
  '/manifest.json',
  '/favicon.ico',
  '/logo192.png',
  '/logo512.png',
  '/icon-144x144.png',
  '/icon-256x256.png',
  '/icon-384x384.png',
  '/apple-touch-icon.png',
  '/chesscrew-1024x1024.png'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Caching static assets');
        return cache.addAll(STATIC_ASSETS.map(url => new Request(url, {
          credentials: 'same-origin'
        })));
      })
      .catch((error) => {
        console.error('Failed to cache static assets:', error);
      })
  );
  // Force the waiting service worker to become the active service worker
  self.skipWaiting();
});

// Listen for skip waiting message from client
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Delete any cache that doesn't match current version
          if (cacheName.startsWith('chesscrew-') &&
              cacheName !== CACHE_NAME &&
              cacheName !== API_CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  // Ensure the service worker takes control of all pages immediately
  self.clients.claim();
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', (event) => {
  // Only handle GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Skip non-http(s) requests
  if (!event.request.url.startsWith('http')) {
    return;
  }

  const url = new URL(event.request.url);
  const isApiRequest = url.pathname.startsWith('/api/');

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version if available
        if (response) {
          console.log('Serving from cache:', event.request.url);
          return response;
        }

        // For API requests, use network-first strategy except for players and tournaments
        if (isApiRequest) {
          const isPlayersOrTournaments = url.pathname.includes('/api/players') || url.pathname.includes('/api/tournaments');

          if (!isPlayersOrTournaments) {
            // Network-first for other API requests
            return fetch(event.request).then((networkResponse) => {
              // Don't cache non-200 responses (including 403)
              if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                return networkResponse;
              }

              // Cache successful API responses
              const responseToCache = networkResponse.clone();
              caches.open(API_CACHE_NAME)
                .then((cache) => {
                  cache.put(event.request, responseToCache);
                });

              return networkResponse;
            }).catch((error) => {
              console.log('Network request failed, trying cache:', error);
              // If network fails, try cache
              return caches.match(event.request);
            });
          }
        }

        // For static assets, use cache-first strategy
        return fetch(event.request).then((networkResponse) => {
          // Don't cache non-200 responses
          if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
            return networkResponse;
          }

          // Cache successful responses
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(event.request, responseToCache);
            });

          return networkResponse;
        }).catch((error) => {
          console.log('Network request failed:', error);
          // If both network and cache fail, return offline page or error
          return new Response('Offline - Content not available', {
            status: 503,
            statusText: 'Service Unavailable'
          });
        });
      })
  );
});