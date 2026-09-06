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

export function getWatchlistChanges(id) {
  return apiRequest(`/watchlists/${id}/changes`)
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

export function addStockToWatchlist(watchlistId, stockId) {
  return apiRequest(`/watchlists/${watchlistId}/stocks`, {
    method: 'POST',
    body: JSON.stringify({ stock_id: stockId }),
  })
}

export function removeStockFromWatchlist(watchlistId, stockId) {
  return apiRequest(`/watchlists/${watchlistId}/stocks/${stockId}`, { method: 'DELETE' })
}
