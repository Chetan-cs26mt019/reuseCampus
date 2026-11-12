import { useEffect, useState } from 'react'
import {
  ArrowUpRight,
  Heart,
  Sparkles,
  BookOpen,
  Laptop,
  Armchair,
  Shirt,
  Package,
} from 'lucide-react'
import { apiGet, apiRequest, getItems } from '../../services/api'

const categoryIcons = {
  1: BookOpen,
  2: Laptop,
  3: Armchair,
  4: Shirt,
}

export default function TrendingSection() {
  const [products, setProducts] = useState([])
  const [favourites, setFavourites] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    async function loadProducts() {
      try {
        const data = await apiGet('/recommendations/popular')
        const items = getItems(data)

        const productsWithImages = await Promise.all(
          items.map(async (product) => {
            try {
              const imageData = await apiGet(`/listings/${product.id}/images`)
              return {
                ...product,
                image_url: getItems(imageData)[0]?.image_url || null,
              }
            } catch {
              return { ...product, image_url: null }
            }
          })
        )

        setProducts(productsWithImages)

        if (localStorage.getItem('access_token')) {
          try {
            const saved = await apiGet('/favourites')
            setFavourites(getItems(saved).map((item) => item.id))
          } catch {
            setFavourites([])
          }
        }
      } catch (err) {
        console.error('Popular listings:', err)
        setError(true)
      } finally {
        setLoading(false)
      }
    }

    loadProducts()
  }, [])

  async function toggleFavourite(listingId) {
    if (!localStorage.getItem('access_token')) {
      window.location.assign('/login')
      return
    }

    const alreadySaved = favourites.includes(listingId)

    setFavourites((current) =>
      alreadySaved
        ? current.filter((id) => id !== listingId)
        : [...current, listingId]
    )

    try {
      await apiRequest(`/listings/${listingId}/favourite`, {
        method: alreadySaved ? 'DELETE' : 'POST',
      })
    } catch (err) {
      setFavourites((current) =>
        alreadySaved
          ? [...current, listingId]
          : current.filter((id) => id !== listingId)
      )
      console.error('Unable to update wishlist:', err)
    }
  }

  return (
    <section className="section trending-section" id="trending">
      <div className="section-heading">
        <div>
          <span className="eyebrow">STUDENT FAVOURITES</span>
          <h2>Trending on Campus</h2>
          <p>Discover popular finds from your campus community.</p>
        </div>
        <a href="/browse" className="text-link">Explore all →</a>
      </div>

      {loading && <p className="section-message">Loading popular products...</p>}

      {error && (
        <p className="section-message">
          Unable to load products. Please try again later.
        </p>
      )}

      {!loading && !error && products.length === 0 && (
        <p className="section-message">No popular products available yet.</p>
      )}

      {!loading && !error && products.length > 0 && (
        <div className="product-grid">
          {products.slice(0, 4).map((product) => {
            const ProductIcon = categoryIcons[product.category_id] || Package
            const isFavourite = favourites.includes(product.id)

            return (
              <article className="product-card" key={product.id}>
                <a href={`/listings/${product.id}`} className="product-image">
                  {product.image_url ? (
                    <img src={product.image_url} alt={product.title} />
                  ) : (
                    <ProductIcon className="product-placeholder-icon" />
                  )}
                  <span className="condition-tag">
                    {product.condition || 'Pre-loved'}
                  </span>
                </a>

                <div className="product-info">
                  <div className="product-title-row">
                    <h3>{product.title}</h3>
                    <button
                      type="button"
                      className={`icon-button ${isFavourite ? 'favourite-active' : ''}`}
                      aria-label={isFavourite ? 'Remove from wishlist' : 'Add to wishlist'}
                      aria-pressed={isFavourite}
                      onClick={() => toggleFavourite(product.id)}
                    >
                      <Heart
                        size={19}
                        fill={isFavourite ? 'currentColor' : 'none'}
                      />
                    </button>
                  </div>

                  <strong className="product-price">
                    ₹{Number(product.price || 0).toLocaleString('en-IN')}
                  </strong>

                  <a href={`/listings/${product.id}`} className="product-link">
                    View details <ArrowUpRight size={16} />
                  </a>
                </div>
              </article>
            )
          })}
        </div>
      )}

      <div className="recommendation-banner">
        <div className="recommendation-icon">
          <Sparkles size={26} />
        </div>
        <div>
          <span>SMARTER CAMPUS SHOPPING</span>
          <h3>Discover recommendations picked for you.</h3>
          <p>Explore suggestions based on popular campus finds.</p>
        </div>
        <a href="/recommendations">Explore recommendations →</a>
      </div>
    </section>
  )
}
