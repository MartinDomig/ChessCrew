// src/api.js
const API_URL = process.env.REACT_APP_API_URL;

export async function apiFetch(endpoint, options = {}) {
  const method = options.method ? options.method.toUpperCase() : 'GET';
  let headers = { ...(options.headers || {}) };
  let body = options.body;
  
  // Handle body serialization
  if (['POST', 'PUT', 'PATCH'].includes(method) && body && typeof body === 'object') {
    const isFormData = body instanceof FormData;
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
      body = JSON.stringify(body);
    }
  }
  
  const opts = { ...options, headers, body, credentials: 'include' };
  const res = await fetch(`${API_URL}${endpoint}`, opts);
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
  return res.json();
}
