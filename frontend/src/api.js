// src/api.js
const API_URL = process.env.REACT_APP_API_URL;

export async function apiFetch(endpoint, options = {}) {
  const res = await fetch(`${API_URL}${endpoint}`, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Network response was not ok');
  }
  return res.json();
}
