import { apiRequest } from './api'

export function loginRequest(email, password) {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function signupRequest(name, email, password) {
  return apiRequest('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  })
}

export function getCurrentUser() {
  return apiRequest('/auth/me')
}

export function logoutRequest() {
  return apiRequest('/auth/logout', { method: 'POST' })
}
