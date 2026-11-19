import { useCallback, useEffect, useState } from 'react'
import { Package } from 'lucide-react'
import { apiGet, getItems } from '../../services/api'

async function addListingImages(items) {
  return Promise.all(items.map(async (item) => {
    try {
      const imageData = await apiGet(`/listings/${item.id}/images`)
      return { ...item, image_url: getItems(imageData)[0]?.image_url || null }
    } catch {
      return { ...item, image_url: null }
    }
  }))
}

export default function Recommendations() {
  const isLoggedIn = Boolean(localStorage.getItem('access_token'))
  const [mode, setMode] = useState('popular')
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async (selectedMode) => {
    setLoading(true)
    setError('')
    setItems([])

    try {
      const endpoint = selectedMode === 'personalized'
        ? '/recommendations'
        : '/recommendations/popular'
      const data = await apiGet(endpoint)
      const products = await addListingImages(getItems(data))
      setItems(products)
    } catch (err) {
      setError(err.message || 'Unable to load recommendations.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load('popular')
    }, 0)

    return () => window.clearTimeout(timer)
  }, [load])

  function selectMode(nextMode) {
    setMode(nextMode)
    load(nextMode)
  }

  return (
    <section className="section page-section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">DISCOVER CAMPUS FINDS</span>
          <h2>Recommendations</h2>
          <p>Explore popular listings or suggestions shaped by your activity.</p>
        </div>
      </div>

      <div className="feature-actions" role="tablist" aria-label="Recommendation type">
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'popular'}
          className={mode === 'popular' ? 'active' : ''}
          onClick={() => selectMode('popular')}
        >
          Popular Items
        </button>
        {isLoggedIn && (
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'personalized'}
            className={mode === 'personalized' ? 'active' : ''}
            onClick={() => selectMode('personalized')}
          >
            For You
          </button>
        )}
      </div>

      {loading && <p className="section-message">Loading recommendations...</p>}
      {error && <p className="form-error" role="alert">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <div className="section-message">
          {mode === 'personalized'
            ? 'Your recommendations are getting started. Browse listings, search for items or save favourites, and we will use those interests to suggest relevant finds.'
            : 'No popular listings are available right now.'}
        </div>
      )}

      {!loading && !error && items.length > 0 && (
        <div className="product-grid">
          {items.map((item) => (
            <article className="product-card" key={item.id}>
              <a href={`/listings/${item.id}`} className="product-image">
                {item.image_url
                  ? <img src={item.image_url} alt={item.title} />
                  : <Package className="product-placeholder-icon" />}
                <span className="condition-tag">{item.condition || 'Pre-loved'}</span>
              </a>
              <div className="product-info">
                <h3>{item.title}</h3>
                <strong className="product-price">
                  ₹{Number(item.price || 0).toLocaleString('en-IN')}
                </strong>
                {item.recommendation_reason && <p>{item.recommendation_reason}</p>}
                <a className="product-link" href={`/listings/${item.id}`}>
                  View details →
                </a>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
