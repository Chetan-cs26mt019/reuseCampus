const API_BASE = '/api'
const TOKEN_KEY = 'access_token'

export async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem(TOKEN_KEY)
  const isFormData = options.body instanceof FormData

  const headers = {
    ...(!isFormData && options.body
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

    const message =
      data?.error?.message ||
      data?.detail ||
      `Request failed: ${response.status}`

    throw new Error(message)
  }

  if (response.status === 204) {
    return null
  }

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
