import { apiRequest } from './api'

export function getDashboardSummary() {
  return apiRequest('/dashboard/summary')
}

export function loginUser(email, password) {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}
