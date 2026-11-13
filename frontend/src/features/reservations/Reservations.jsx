import { useCallback, useEffect, useState } from 'react'
import { apiRequest } from '../../services/api'

export default function Reservations() {
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const user = (() => { try { return JSON.parse(localStorage.getItem('current_user') || 'null') } catch { return null } })()

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
      {error && <p className="form-error">{error}</p>}
      {loading ? <p>Loading reservations...</p> : items.length === 0
        ? <p>No reservations yet.</p>
        : items.map((item) => (
          <article className="feature-card" key={item.id}>
            <div className="reservation-product">{item.listing_image ? <img src={item.listing_image} alt={item.listing_title || 'Product'} /> : <span className="product-thumb-placeholder">📦</span>}<div><strong>{item.listing_title || 'Product reservation'}</strong><p>{item.listing_price != null ? `INR ${Number(item.listing_price).toLocaleString('en-IN')} · ` : ''}Status: <strong>{item.status}</strong></p></div></div>
            <p>{Number(item.seller_id) === Number(user?.id) ? `Buyer: ${item.buyer_name}` : `Seller: ${item.seller_name}`}</p>
            <div className="feature-actions">
              {Number(item.seller_id) === Number(user?.id) && item.status === 'requested' && ['accept', 'reject'].map((action) => (
                <button key={action} onClick={() => update(item.id, action)}>{action}</button>
              ))}
              {item.status === 'accepted' && (
                <button onClick={() => update(item.id, 'complete')}>Mark completed</button>
              )}
              {Number(item.buyer_id) === Number(user?.id) && item.status === 'requested' && (
                <button onClick={() => update(item.id, 'cancel')}>Cancel request</button>
              )}
              <a href={`/listings/${item.listing_id}`}>View product</a>
            </div>
          </article>
        ))}
    </section>
  )
}
