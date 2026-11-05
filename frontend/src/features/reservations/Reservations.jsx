import { useCallback, useEffect, useState } from 'react'
import { apiRequest } from '../../services/apiClient'

export default function Reservations() {
  const [items, setItems] = useState([])
  const [listingId, setListingId] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const data = await apiRequest('/orders')
      setItems(data.items || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => load(), 0)
    return () => clearTimeout(timer)
  }, [load])

  async function create(event) {
    event.preventDefault()
    try {
      await apiRequest('/orders', {
        method: 'POST',
        body: JSON.stringify({ listing_id: Number(listingId) }),
      })
      setListingId('')
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function update(id, action) {
    try {
      await apiRequest(`/orders/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ action }),
      })
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="section page-section">
      <h2>Reservations</h2>
      <form className="feature-form" onSubmit={create}>
        <input type="number" min="1" required placeholder="Listing ID"
          value={listingId} onChange={(e) => setListingId(e.target.value)} />
        <button>Request reservation</button>
      </form>
      {error && <p className="form-error">{error}</p>}
      {loading ? <p>Loading reservations...</p> : items.length === 0
        ? <p>No reservations yet.</p>
        : items.map((item) => (
          <article className="feature-card" key={item.id}>
            <strong>Reservation #{item.id}</strong>
            <p>Listing: {item.listing_id} · Status: {item.status}</p>
            <div className="feature-actions">
              {['accept', 'reject', 'cancel', 'complete'].map((action) => (
                <button key={action} onClick={() => update(item.id, action)}>
                  {action}
                </button>
              ))}
            </div>
          </article>
        ))}
    </section>
  )
}
