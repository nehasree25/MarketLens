import { apiRequest } from './api'

export function getWatchlists() {
  return apiRequest('/watchlists')
}

export function createWatchlist(data) {
  return apiRequest('/watchlists', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function getWatchlist(id) {
  return apiRequest(`/watchlists/${id}`)
}

export function renameWatchlist(id, data) {
  return apiRequest(`/watchlists/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function deleteWatchlist(id) {
  return apiRequest(`/watchlists/${id}`, { method: 'DELETE' })
}
