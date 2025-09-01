// src/api.js
const API_URL = process.env.REACT_APP_API_URL;

export async function apiFetch(endpoint, options = {}) {
  const method = options.method ? options.method.toUpperCase() : 'GET';
  let headers = { ...(options.headers || {}) };
  // Only set Content-Type: application/json if body is a plain object
  if (['POST', 'PUT', 'PATCH'].includes(method)) {
    const isFormData = options.body instanceof FormData;
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
  }
  const opts = { ...options, headers, credentials: 'include' };
  const res = await fetch(`${API_URL}${endpoint}`, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Network response was not ok');
  }
  if (res.status === 204) {
    return null;
  }
  return res.json();
}
