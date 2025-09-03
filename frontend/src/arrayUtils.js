/**
 * Utility functions for handling arrays that may be corrupted by cache serialization
 */

/**
 * Reconstructs an array from potentially corrupted cache data
 * Handles cases where arrays are deserialized as objects with numeric keys
 * 
 * @param {any} data - The data to reconstruct as an array
 * @param {string} fallbackProperty - Optional property name to check for nested array data
 * @returns {Array} - Reconstructed array, or empty array if reconstruction fails
 */
export function reconstructArray(data, fallbackProperty = null) {
  // If data is null/undefined, return empty array
  if (!data) {
    return [];
  }

  // If already an array, use it directly
  if (Array.isArray(data)) {
    return data.slice(); // Return a copy to avoid mutations
  }

  // If data is an object, try to reconstruct
  if (typeof data === 'object') {
    // Filter out cache metadata keys
    const keys = Object.keys(data).filter(key => key !== '_isStale' && key !== '_cacheAge');
    const isArrayLike = keys.length > 0 && keys.every(key => /^\d+$/.test(key));
    
    if (isArrayLike) {
      // Convert array-like object to proper array
      const maxIndex = Math.max(...keys.map(k => parseInt(k, 10)));
      return Array.from({ length: maxIndex + 1 }, (_, i) => data[i]).filter(item => item !== undefined);
    }
    
    // Check for nested array properties
    if (fallbackProperty && Array.isArray(data[fallbackProperty])) {
      return data[fallbackProperty];
    }
    
    // Check common nested array properties
    if (Array.isArray(data.data)) {
      return data.data;
    }
    
    // Try to extract from destructured cache metadata
    const { _isStale, _cacheAge, ...rest } = data;
    if (Array.isArray(rest)) {
      return rest;
    }
  }

  // If all else fails, return empty array
  console.warn('Could not reconstruct array from data:', data);
  return [];
}

/**
 * Extracts cache metadata and reconstructed array from cache response
 * 
 * @param {any} data - The cached response data
 * @param {string} fallbackProperty - Optional property name for nested array data
 * @returns {Object} - Object with { array, isStale } properties
 */
export function extractArrayWithMetadata(data, fallbackProperty = null) {
  const isStale = data?._isStale === true;
  const array = reconstructArray(data, fallbackProperty);
  
  return { array, isStale };
}
