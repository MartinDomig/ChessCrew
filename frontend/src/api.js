// src/api.js
const API_URL = process.env.REACT_APP_API_URL;

// Cache configuration
const CACHE_NAME = 'chesscrew-api-cache-v1';
const CACHE_EXPIRY = 5 * 60 * 1000; // 5 minutes in milliseconds
const OFFLINE_CACHE_EXPIRY = 24 * 60 * 60 * 1000; // 24 hours for offline mode

// Helper function to check if we're online
const isOnline = () => navigator.onLine;

// Helper function to create cache key
const createCacheKey = (endpoint, options = {}) => {
  const method = options.method ? options.method.toUpperCase() : 'GET';
  const params = new URLSearchParams(options.params || {}).toString();
  const queryString = params ? `?${params}` : '';
  
  // Create a proper cache key that can be used as a URL
  const cacheKey = `api/${method.toLowerCase()}${endpoint}${queryString}`;
  
  // Ensure it starts with a valid path
  return cacheKey.startsWith('/') ? cacheKey.slice(1) : cacheKey;
};

// Helper function to get cached data
const getCachedData = async (cacheKey) => {
  try {
    const cache = await caches.open(CACHE_NAME);
    const cacheUrl = `https://api-cache.local/${cacheKey}`;
    const cachedResponse = await cache.match(cacheUrl);
    
    if (cachedResponse) {
      const cachedData = await cachedResponse.json();
      
      if (cachedData._cacheTimestamp) {
        const age = Date.now() - cachedData._cacheTimestamp;
        const effectiveExpiry = isOnline() ? CACHE_EXPIRY : OFFLINE_CACHE_EXPIRY;
        
        // Check if cache is still valid (different expiry times for online/offline)
        if (age < effectiveExpiry) {
          // Remove cache metadata before returning
          const { _cacheTimestamp, ...data } = cachedData;
          
          // Check if data is an array-like object (has numeric keys) and convert it back to array
          if (data && typeof data === 'object' && !Array.isArray(data)) {
            const keys = Object.keys(data);
            const isArrayLike = keys.length > 0 && keys.every(key => /^\d+$/.test(key)) && 
                               'length' in data && typeof data.length === 'number';
            
            if (isArrayLike) {
              // Convert array-like object back to proper array
              const reconstructedArray = Array.from({ length: data.length }, (_, i) => data[i]);
              console.log('Reconstructed array from cached object:', reconstructedArray.length);
              
              // Add metadata to indicate if data is stale (expired by online standards but valid offline)
              if (!isOnline() && age > CACHE_EXPIRY) {
                reconstructedArray._isStale = true;
                reconstructedArray._cacheAge = age;
              }
              
              return reconstructedArray;
            }
          }
          
          // Add metadata to indicate if data is stale (expired by online standards but valid offline)
          if (!isOnline() && age > CACHE_EXPIRY) {
            // If data is an array, we need to add metadata differently
            if (Array.isArray(data)) {
              // Create a new array with metadata properties
              const staleArray = [...data];
              staleArray._isStale = true;
              staleArray._cacheAge = age;
              return staleArray;
            } else {
              return {
                ...data,
                _isStale: true,
                _cacheAge: age
              };
            }
          }
          
          return data;
        }
      }
    }
  } catch (error) {
    console.warn('Cache retrieval failed:', error);
  }
  return null;
};

// Helper function to cache data
const cacheData = async (cacheKey, data) => {
  try {
    const cache = await caches.open(CACHE_NAME);
    
    // Add timestamp to cached data
    const dataWithTimestamp = {
      ...data,
      _cacheTimestamp: Date.now()
    };
    
    // Create a proper URL for the cache key
    const cacheUrl = `https://api-cache.local/${cacheKey}`;
    
    // Create a response object to store in cache
    const response = new Response(JSON.stringify(dataWithTimestamp), {
      headers: {
        'Content-Type': 'application/json',
        'X-Cached': 'true'
      }
    });
    
    await cache.put(cacheUrl, response);
    console.log(`Cached: ${cacheKey}`);
  } catch (error) {
    console.warn('Cache storage failed:', error);
  }
};

// Helper function to clear expired cache entries
const clearExpiredCache = async () => {
  try {
    const cache = await caches.open(CACHE_NAME);
    const keys = await cache.keys();
    
    for (const request of keys) {
      const response = await cache.match(request);
      if (response) {
        const data = await response.json();
        if (data._cacheTimestamp) {
          const age = Date.now() - data._cacheTimestamp;
          const effectiveExpiry = isOnline() ? CACHE_EXPIRY : OFFLINE_CACHE_EXPIRY;
          
          // Only delete if expired beyond the effective expiry time
          if (age > effectiveExpiry) {
            await cache.delete(request);
          }
        }
      }
    }
  } catch (error) {
    console.warn('Cache cleanup failed:', error);
  }
};

// Main API fetch function with caching
export async function apiFetch(endpoint, options = {}) {
  const method = options.method ? options.method.toUpperCase() : 'GET';
  let headers = { ...(options.headers || {}) };
  let body = options.body;
  
  console.log(`API Fetch: ${method} ${endpoint}`);

  // Check if we're offline and trying to make a write request
  if (!isOnline() && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    throw new Error('Cannot perform write operations while offline. Please check your internet connection.');
  }
  
  // Handle body serialization
  if (['POST', 'PUT', 'PATCH'].includes(method) && body && typeof body === 'object') {
    const isFormData = body instanceof FormData;
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
      body = JSON.stringify(body);
    }
  }
  
  const cacheKey = createCacheKey(endpoint, options);
  console.log('Using cache key:', cacheKey);
  
  // For GET requests, try to serve from cache first if offline
  if (method === 'GET') {
    // If offline, return cached data if available (even if stale)
    if (!isOnline()) {
      const cachedData = await getCachedData(cacheKey);
      if (cachedData) {
        if (cachedData._isStale) {
          console.log(`Serving stale cached data for ${endpoint} (offline, ${Math.floor(cachedData._cacheAge / 60000)}m old)`);
        } else {
          console.log(`Serving cached data for ${endpoint} (offline)`);
        }
        return cachedData;
      } else {
        throw new Error('No cached data available and you are offline. Please check your internet connection.');
      }
    }
    
    // If online, check cache first for faster response
    const cachedData = await getCachedData(cacheKey);
    if (cachedData) {
      console.log(`Serving cached data for ${endpoint} (fast load)`);
      
      // Return cached data immediately, but fetch fresh data in background
      fetchAndUpdateCache(endpoint, options, cacheKey).catch(error => {
        console.warn('Background cache update failed:', error);
      });
      
      return cachedData;
    }
  }
  
  // Make the actual network request
  const opts = { ...options, headers, body, credentials: 'include' };
  
  try {
    const res = await fetch(`${API_URL}${endpoint}`, opts);
    
    // Handle 403 Forbidden - user is not authenticated
    if (res.status === 403) {
      console.log('Received 403 Forbidden - clearing cache and marking as logged out');
      // Clear API cache when we get 403
      await clearApiCache();
      // Dispatch custom event to notify app of authentication error
      window.dispatchEvent(new CustomEvent('auth-error', { detail: { status: 403 } }));
      // Throw a specific error for 403
      const error = new Error('Authentication required');
      error.status = 403;
      error.isAuthError = true;
      throw error;
    }
    
    if (!res.ok) {
      let errorMessage = 'Network response was not ok';
      try {
        const errorData = await res.json();
        if (errorData.error) {
          errorMessage = errorData.error;
        }
      } catch {
        const text = await res.text();
        errorMessage = text || errorMessage;
      }
      throw new Error(errorMessage);
    }
    
    if (res.status === 204) {
      return null;
    }
    
    const data = await res.json();
    
    // Cache GET requests for future use
    if (method === 'GET' && data) {
      await cacheData(cacheKey, data);
    }
    
    return data;
  } catch (error) {
    // If network fails and we have cached data for GET requests, use it (even if stale when offline)
    if (method === 'GET') {
      const cachedData = await getCachedData(cacheKey);
      if (cachedData) {
        if (cachedData._isStale) {
          console.log(`Network failed, serving stale cached data for ${endpoint} (${Math.floor(cachedData._cacheAge / 60000)}m old)`);
        } else {
          console.log(`Network failed, serving cached data for ${endpoint}`);
        }
        return cachedData;
      }
    }
    throw error;
  }
}

// Background function to fetch and update cache
const fetchAndUpdateCache = async (endpoint, options, cacheKey) => {
  try {
    const headers = { ...(options.headers || {}) };
    const opts = { ...options, headers, credentials: 'include' };
    
    const res = await fetch(`${API_URL}${endpoint}`, opts);
    
    // Handle 403 in background updates too
    if (res.status === 403) {
      console.log('Received 403 in background update - dispatching auth error');
      window.dispatchEvent(new CustomEvent('auth-error', { detail: { status: 403 } }));
      return;
    }
    
    if (res.ok && res.status !== 204) {
      const data = await res.json();
      await cacheData(cacheKey, data);
      console.log(`Cache updated in background for ${endpoint}`);
    }
  } catch (error) {
    console.warn('Background cache update failed:', error);
  }
};

// Function to clear all API cache (useful for logout or manual refresh)
export const clearApiCache = async () => {
  try {
    const cache = await caches.open(CACHE_NAME);
    const keys = await cache.keys();
    await Promise.all(keys.map(key => cache.delete(key)));
    console.log('API cache cleared');
  } catch (error) {
    console.warn('Failed to clear API cache:', error);
  }
};

// Function to get cache status information
export const getCacheInfo = async () => {
  try {
    const cache = await caches.open(CACHE_NAME);
    const keys = await cache.keys();
    
    const cacheInfo = {
      totalEntries: keys.length,
      entries: []
    };
    
    for (const request of keys) {
      try {
        const response = await cache.match(request);
        if (response) {
          const data = await response.json();
          if (data._cacheTimestamp) {
            const age = Date.now() - data._cacheTimestamp;
            const onlineExpired = age > CACHE_EXPIRY;
            const offlineExpired = age > OFFLINE_CACHE_EXPIRY;
            
            let status = 'valid';
            if (offlineExpired) {
              status = 'expired';
            } else if (onlineExpired && !isOnline()) {
              status = 'stale';
            } else if (onlineExpired) {
              status = 'expired';
            }
            
            cacheInfo.entries.push({
              url: request.url,
              timestamp: data._cacheTimestamp,
              expired: offlineExpired,
              stale: onlineExpired && !offlineExpired,
              status: status,
              age: age
            });
          }
        }
      } catch (error) {
        // Skip invalid cache entries
        console.warn('Skipping invalid cache entry:', request.url);
      }
    }
    
    return cacheInfo;
  } catch (error) {
    console.warn('Failed to get cache info:', error);
    return { totalEntries: 0, entries: [] };
  }
};

// Initialize cache cleanup on module load
clearExpiredCache();

// Background preloading function for common/slow endpoints
export const preloadCommonData = async (currentFilter = null) => {
  if (!isOnline()) {
    console.log('Offline - skipping background preload');
    return;
  }

  console.log('Starting background preload of common data: current filter =', currentFilter);
  
  // Only preload full players list if we're currently showing active-only players
  // This avoids loading both lists at startup when user wants full list
  if (currentFilter === 'active') {
    // User is viewing active players, preload full list for when they switch
    apiFetch('/players')
      .then(() => {
        console.log('Background preload: Full players list cached');
      })
      .catch(error => {
        console.warn('Background preload failed for players:', error.message);
      });
  } else if (currentFilter === 'all') {
    // User is viewing full list, preload active-only for when they filter
    apiFetch('/players?active=true')
      .then(() => {
        console.log('Background preload: Active players list cached');
      })
      .catch(error => {
        console.warn('Background preload failed for active players:', error.message);
      });
  }

  // Always preload tournaments as it's fast and commonly used
  apiFetch('/tournaments')
    .then(() => {
      console.log('Background preload: Tournaments list cached');
    })
    .catch(error => {
      console.warn('Background preload failed for tournaments:', error.message);
    });
};

// Invalidate related caches when a player is updated
export const invalidatePlayerCaches = async (playerId = null) => {
  if ('caches' in window) {
    try {
      const cacheNames = await caches.keys();
      for (const cacheName of cacheNames) {
        if (cacheName.includes('chesscrew-api-cache')) {
          const cache = await caches.open(cacheName);
          const keys = await cache.keys();
          for (const request of keys) {
            const url = new URL(request.url);
            // Invalidate players list caches when a player is updated
            if (url.pathname.includes('/players') && !url.pathname.includes('/players/')) {
              await cache.delete(request);
              console.log('Invalidated players list cache:', url.pathname);
            }
            // If a specific player ID is provided, also invalidate that player's individual cache
            if (playerId && url.pathname.includes(`/players/${playerId}`)) {
              await cache.delete(request);
              console.log('Invalidated individual player cache:', url.pathname);
            }
          }
        }
      }
    } catch (error) {
      console.warn('Failed to invalidate player caches:', error);
    }
  }
};
