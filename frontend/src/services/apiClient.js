const API_BASE = '/api'

export async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('access_token')
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
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `Request failed: ${response.status}`)
  }

  if (response.status === 204) return null

  return response.json()
}
