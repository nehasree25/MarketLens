const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const REQUEST_TIMEOUT_MS = 15000

function friendlyMessage(status) {
  if (status === 401) return 'Your session has expired. Please log in again.'
  if (status === 403) return "You don't have permission to perform this action."
  if (status === 404) return 'The requested information could not be found.'
  if (status === 422) return 'Please check the information and try again.'
  if (status === 429) return 'Too many requests. Please try again shortly.'
  if (status >= 500) return 'MarketLens is temporarily unavailable. Please try again.'
  return 'Unable to complete the request. Please try again.'
}

export async function apiRequest(path, options = {}) {
  const token = localStorage.getItem('marketlens_token')
  const headers = new Headers(options.headers || {})
  headers.set('Accept', 'application/json')

  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  if (token) headers.set('Authorization', `Bearer ${token}`)

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers, signal: options.signal || controller.signal })
  } catch (requestError) {
    const error = new Error(requestError.name === 'AbortError' ? 'The request took too long. Please try again.' : 'Unable to connect to MarketLens. Check your connection and try again.')
    error.status = 0
    error.userMessage = error.message
    throw error
  } finally {
    clearTimeout(timeout)
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const error = new Error(friendlyMessage(response.status))
    error.status = response.status
    error.userMessage = friendlyMessage(response.status)
    error.backendDetail = payload?.detail
    throw error
  }

  if (response.status === 204) return null
  try {
    return await response.json()
  } catch {
    const error = new Error('MarketLens returned an unexpected response. Please try again.')
    error.status = response.status
    error.userMessage = error.message
    throw error
  }
}

export function clearSession() {
  localStorage.removeItem('marketlens_token')
}
