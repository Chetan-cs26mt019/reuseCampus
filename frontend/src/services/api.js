const API_BASE = '/api'
const TOKEN_KEY = 'access_token'

export async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem(TOKEN_KEY)

  const headers = {
    ...(options.body && !(options.body instanceof FormData)
      ? { 'Content-Type': 'application/json' }
      : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || `Request failed: ${response.status}`)
  }

  if (response.status === 204) return null
  return response.json()
}

export const apiGet = (endpoint) => apiRequest(endpoint)

export function getItems(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.items)) return data.items
  if (Array.isArray(data?.categories)) return data.categories
  if (Array.isArray(data?.listings)) return data.listings
  return []
}
