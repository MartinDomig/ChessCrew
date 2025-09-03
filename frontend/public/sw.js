// Cache version - update this when deploying new code
const CACHE_VERSION = 'v1756926220659';
const CACHE_NAME = 'chesscrew-' + CACHE_VERSION;
const API_CACHE_NAME = 'chesscrew-api-cache-' + CACHE_VERSION;
const STATIC_ASSETS = [
  '/',
  '/static/js/main.b37dc3c3.js',
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

        // For API requests, try the API cache
        if (isApiRequest) {
          return caches.open(API_CACHE_NAME).then(apiCache => {
            return apiCache.match(event.request).then(apiResponse => {
              if (apiResponse) {
                console.log('Serving API from cache:', event.request.url);
                return apiResponse;
              }

              // If not in cache, fetch from network and cache if successful
              return fetch(event.request).then((response) => {
                if (!response || response.status !== 200 || response.type !== 'basic') {
                  return response;
                }

                const responseToCache = response.clone();
                apiCache.put(event.request, responseToCache);
                return response;
              });
            });
          });
        }

        // Otherwise, fetch from network for non-API requests
        return fetch(event.request).then((response) => {
          // Don't cache non-successful responses
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response as it's a stream and can only be consumed once
          const responseToCache = response.clone();

          // Cache the response for future requests
          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(event.request, responseToCache);
            });

          return response;
        });
      })
      .catch(() => {
        // If both cache and network fail, return a fallback page for navigation requests
        if (event.request.destination === 'document') {
          return caches.match('/').then(cachedRoot => {
            if (cachedRoot) {
              return cachedRoot;
            }
            // If no cached root, return a basic offline page
            return new Response(
              `<!DOCTYPE html>
              <html>
              <head>
                <title>ChessCrew - Offline</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
              </head>
              <body>
                <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
                  <h1>You're Offline</h1>
                  <p>ChessCrew is not available right now. Please check your internet connection and try again.</p>
                  <button onclick="window.location.reload()">Retry</button>
                </div>
              </body>
              </html>`,
              {
                headers: { 'Content-Type': 'text/html' }
              }
            );
          });
        }
        
        // For non-document requests that fail, return a proper error response
        return new Response('Service Unavailable', { 
          status: 503, 
          statusText: 'Service Unavailable' 
        });
      })
  );
});

// Handle background sync for when the app comes back online
self.addEventListener('sync', (event) => {
  console.log('Background sync triggered:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(
      // Add any background sync logic here if needed
      Promise.resolve()
    );
  }
});

// Handle push notifications (if needed in the future)
self.addEventListener('push', (event) => {
  console.log('Push notification received');
  
  const options = {
    body: event.data ? event.data.text() : 'New update available!',
    icon: '/icon-256x256.png',
    badge: '/icon-144x144.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '1'
    },
    actions: [
      {
        action: 'explore',
        title: 'Open ChessCrew',
        icon: '/icon-256x256.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/icon-256x256.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('ChessCrew', options)
  );
});
