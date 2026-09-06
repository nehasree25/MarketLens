import { apiRequest } from './api'

export function getStocks(skip = 0, limit = 5) {
  return apiRequest(`/stocks?skip=${skip}&limit=${limit}`)
}

export function searchStocks(query, skip = 0, limit = 5) {
  return apiRequest(`/stocks/search?q=${encodeURIComponent(query.trim())}&skip=${skip}&limit=${limit}`)
}

export function checkStock(stockId) {
  return apiRequest(`/stocks/${stockId}/check`, { method: 'POST' })
}

export function getStock(stockId) {
  return apiRequest(`/stocks/${stockId}`)
}

export function getMarketData(stockId) {
  return apiRequest(`/market-data/${stockId}`)
}

export function getStockState(stockId) {
  return apiRequest(`/stocks/${stockId}/state`)
}

export function getStockChanges(stockId) {
  return apiRequest(`/stocks/${stockId}/changes`)
}

export function getStockAttention(stockId) {
  return apiRequest(`/stocks/${stockId}/attention`)
}
