const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export async function apiRequest(path, options = {}) {
  const token = localStorage.getItem('marketlens_token')
  const headers = new Headers(options.headers || {})
  headers.set('Accept', 'application/json')

  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  if (token) headers.set('Authorization', `Bearer ${token}`)

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  } catch {
    const error = new Error('Network request failed')
    error.status = 0
    throw error
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const detail = payload?.detail
    const error = new Error(detail || 'Request failed')
    error.status = response.status
    throw error
  }

  return response.status === 204 ? null : response.json()
}

export function clearSession() {
  localStorage.removeItem('marketlens_token')
}
