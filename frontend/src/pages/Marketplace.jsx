import { useCallback, useEffect, useState } from 'react'
import { apiGet, getItems } from '../services/api'

export default function Marketplace() {
  const [listings, setListings] = useState([])
  const [categories, setCategories] = useState([])
  const [query, setQuery] = useState(
    new URLSearchParams(window.location.search).get('q') || ''
  )
  const [categoryId, setCategoryId] = useState(
    new URLSearchParams(window.location.search).get('category') || ''
  )
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadListings = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const params = new URLSearchParams()
      if (query.trim()) params.set('q', query.trim())
      if (categoryId) params.set('category_id', categoryId)

      const data = await apiGet(`/listings?${params.toString()}`)
      const items = getItems(data)

      const withImages = await Promise.all(items.map(async (item) => {
        try {
          const images = await apiGet(`/listings/${item.id}/images`)
          return { ...item, image_url: getItems(images)[0]?.image_url || '' }
        } catch {
          return { ...item, image_url: '' }
        }
      }))

      setListings(withImages)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [query, categoryId])

  useEffect(() => {
    apiGet('/categories')
      .then((data) => setCategories(getItems(data)))
      .catch(() => {})
    const timer = setTimeout(() => {
      loadListings()
    }, 0)

    return () => clearTimeout(timer)
  }, [loadListings])

  function submitSearch(event) {
    event.preventDefault()
    loadListings()
  }

  return (
    <section className="section page-section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">CAMPUS MARKETPLACE</span>
          <h2>Browse Listings</h2>
          <p>Find useful items shared by your campus community.</p>
        </div>
      </div>

      <form className="marketplace-filters" onSubmit={submitSearch}>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search listings..."
        />
        <select value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
          <option value="">All categories</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>{category.name}</option>
          ))}
        </select>
        <button type="submit">Search</button>
      </form>

      {loading && <p className="section-message">Loading listings...</p>}
      {error && <p className="section-message">{error}</p>}
      {!loading && !error && listings.length === 0 &&
        <p className="section-message">No listings found.</p>}

      {!loading && listings.length > 0 && (
        <div className="product-grid">
          {listings.map((item) => (
            <article className="product-card" key={item.id}>
              <a href={`/listings/${item.id}`} className="product-image">
                {item.image_url
                  ? <img src={item.image_url} alt={item.title} />
                  : <span>📦</span>}
                <span className="condition-tag">{item.condition}</span>
              </a>
              <div className="product-info">
                <h3>{item.title}</h3>
                <strong className="product-price">
                  {item.currency || 'INR'} {Number(item.price).toLocaleString('en-IN')}
                </strong>
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
