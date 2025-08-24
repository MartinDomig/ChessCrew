// src/api.js
const API_URL = process.env.REACT_APP_API_URL;

export async function apiFetch(endpoint, options = {}) {
  const method = options.method ? options.method.toUpperCase() : 'GET';
  const needsJson = ['POST', 'PUT', 'PATCH'].includes(method);
  const headers = {
    ...(needsJson ? { 'Content-Type': 'application/json' } : {}),
    ...(options.headers || {})
  };
  const opts = { ...options, headers };
  const res = await fetch(`${API_URL}${endpoint}`, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Network response was not ok');
  }
  return res.json();
}
