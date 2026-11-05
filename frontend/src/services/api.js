const API_BASE = '/api'

export async function apiGet(endpoint) {
  const response = await fetch(`${API_BASE}${endpoint}`)

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }

  return response.json()
}

export function getItems(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.items)) return data.items
  if (Array.isArray(data?.categories)) return data.categories
  if (Array.isArray(data?.listings)) return data.listings
  return []
}
