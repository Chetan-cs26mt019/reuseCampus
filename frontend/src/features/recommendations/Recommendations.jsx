import { useCallback, useEffect, useState } from 'react'
import { apiRequest } from '../../services/api'

export default function Recommendations() {
  const [mode, setMode] = useState('popular')
  const [listingId, setListingId] = useState('')
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const load = useCallback(async (selectedMode = mode) => {
    setLoading(true)
    setError('')

    let endpoint = '/recommendations/popular'
    if (selectedMode === 'personalized') endpoint = '/recommendations'
    if (selectedMode === 'similar') {
      if (!listingId) {
        setError('Enter a listing ID to find similar listings.')
        setLoading(false)
        return
      }
      endpoint = `/recommendations/similar/${listingId}`
    }

    try {
      const data = await apiRequest(endpoint)
      setItems(data.items || [])
    } catch (err) {
      setError(err.message)
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [mode, listingId])

  useEffect(() => {
    const timer = setTimeout(() => load('popular'), 0)
    return () => clearTimeout(timer)
  }, [load])

  return (
    <section className="section page-section">
      <h2>Recommendations</h2>
      <div className="feature-actions">
        <button onClick={() => { setMode('popular'); load('popular') }}>Popular</button>
        <button onClick={() => { setMode('personalized'); load('personalized') }}>For you</button>
        <button onClick={() => { setMode('similar'); load('similar') }}>Similar listings</button>
      </div>
      {mode === 'similar' && (
        <form className="feature-form" onSubmit={(e) => { e.preventDefault(); load('similar') }}>
          <input type="number" min="1" required placeholder="Listing ID"
            value={listingId} onChange={(e) => setListingId(e.target.value)} />
          <button>Find similar</button>
        </form>
      )}
      {loading && <p>Loading recommendations...</p>}
      {error && <p className="form-error">{error}</p>}
      <div className="product-grid">
        {items.map((item) => (
          <article className="product-card" key={item.id}>
            <div className="product-info">
              <h3>{item.title}</h3>
              <strong className="product-price">
                {item.currency || 'INR'} {Number(item.price).toLocaleString('en-IN')}
              </strong>
              <p>{item.recommendation_reason}</p>
              {item.similarity_score != null &&
                <small>Similarity: {Number(item.similarity_score).toFixed(2)}</small>}
              <a className="product-link" href={`/listings/${item.id}`}>View listing →</a>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
