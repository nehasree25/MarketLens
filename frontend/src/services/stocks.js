import { apiRequest } from './api'

export function getStocks() {
  return apiRequest('/stocks')
}

export function searchStocks(query) {
  return apiRequest(`/stocks/search?q=${encodeURIComponent(query.trim())}`)
}

export function checkStock(stockId) {
  return apiRequest(`/stocks/${stockId}/check`, { method: 'POST' })
}
