import { useCallback, useEffect, useState } from 'react'
import { apiGet, getItems } from '../services/api'

const PAGE_SIZE = 12

export default function Marketplace() {
  const [listings, setListings] = useState([])
  const [categories, setCategories] = useState([])
  const [query, setQuery] = useState(
    new URLSearchParams(window.location.search).get('q') || ''
  )
  const [categoryId, setCategoryId] = useState(
    new URLSearchParams(window.location.search).get('category') || ''
  )
  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [filters, setFilters] = useState({
    query: '',
    categoryId: '',
    minPrice: '',
    maxPrice: '',
  })
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const loadListings = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const params = new URLSearchParams({
        page: String(page),
        size: String(PAGE_SIZE),
      })

      if (filters.query) params.set('q', filters.query)
      if (filters.categoryId) params.set('category_id', filters.categoryId)
      if (filters.minPrice !== '') params.set('min_price', filters.minPrice)
      if (filters.maxPrice !== '') params.set('max_price', filters.maxPrice)

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
      setTotal(data.total ?? items.length)
    } catch (err) {
      setError(err.message)
      setListings([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [filters, page])

  useEffect(() => {
    apiGet('/categories')
      .then((data) => setCategories(getItems(data)))
      .catch(() => {})
  }, [])

  useEffect(() => {
    loadListings()
  }, [loadListings])

  function submitSearch(event) {
    event.preventDefault()

    if (minPrice !== '' && Number(minPrice) < 0) {
      setError('Minimum price cannot be negative.')
      return
    }

    if (maxPrice !== '' && Number(maxPrice) < 0) {
      setError('Maximum price cannot be negative.')
      return
    }

    if (
      minPrice !== '' &&
      maxPrice !== '' &&
      Number(minPrice) > Number(maxPrice)
    ) {
      setError('Minimum price cannot exceed maximum price.')
      return
    }

    setError('')
    setPage(1)
    setFilters({
      query: query.trim(),
      categoryId,
      minPrice,
      maxPrice,
    })
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
        <label>
          Search listings
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search listings..."
          />
        </label>

        <label>
          Category
          <select
            value={categoryId}
            onChange={(event) => setCategoryId(event.target.value)}
          >
            <option value="">All categories</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Minimum price (₹)
          <input
            type="number"
            min="0"
            step="0.01"
            value={minPrice}
            onChange={(event) => setMinPrice(event.target.value)}
            placeholder="No minimum"
          />
        </label>

        <label>
          Maximum price (₹)
          <input
            type="number"
            min="0"
            step="0.01"
            value={maxPrice}
            onChange={(event) => setMaxPrice(event.target.value)}
            placeholder="No maximum"
          />
        </label>

        <button type="submit">Search</button>
      </form>

      {loading && <p className="section-message">Loading listings...</p>}
      {error && <p className="section-message" role="alert">{error}</p>}

      {!loading && !error && listings.length === 0 && (
        <p className="section-message">No listings found.</p>
      )}

      {!loading && listings.length > 0 && (
        <>
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
                    {item.currency || 'INR'}{' '}
                    {Number(item.price).toLocaleString('en-IN')}
                  </strong>
                  <a
                    className="product-link"
                    href={`/listings/${item.id}`}
                  >
                    View details →
                  </a>
                </div>
              </article>
            ))}
          </div>

          <nav className="marketplace-pagination" aria-label="Listing pages">
            <button
              type="button"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={page <= 1 || loading}
            >
              Previous
            </button>

            <span aria-live="polite">
              Page {page} of {totalPages} ({total} listings)
            </span>

            <button
              type="button"
              onClick={() => setPage((current) =>
                Math.min(totalPages, current + 1)
              )}
              disabled={page >= totalPages || loading}
            >
              Next
            </button>
          </nav>
        </>
      )}
    </section>
  )
}
