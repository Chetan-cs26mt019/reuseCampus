import { useEffect, useState } from 'react'
import { Heart, Package } from 'lucide-react'
import { apiGet, apiRequest, getItems } from '../services/api'

export default function ListingCollection({ wishlist = false }) {
  const [listings, setListings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const data = await apiGet(wishlist ? '/favourites' : '/my/listings')
        const items = getItems(data)

        const withImages = await Promise.all(
          items.map(async (item) => {
            try {
              const images = await apiGet(`/listings/${item.id}/images`)
              return {
                ...item,
                image_url: getItems(images)[0]?.image_url || null,
              }
            } catch {
              return { ...item, image_url: null }
            }
          })
        )

        setListings(withImages)
      } catch (err) {
        setError(err.message || 'Unable to load listings.')
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [wishlist])

  async function removeFavourite(id) {
    try {
      await apiRequest(`/listings/${id}/favourite`, { method: 'DELETE' })
      setListings((current) => current.filter((item) => item.id !== id))
    } catch (err) {
      setError(err.message || 'Unable to remove favourite.')
    }
  }

  async function deleteListing(id) {
    if (!window.confirm('Delete this listing? This cannot be undone.')) return
    try {
      await apiRequest(`/listings/${id}`, { method: 'DELETE' })
      setListings((current) => current.filter((item) => item.id !== id))
    } catch (err) { setError(err.message || 'Unable to delete listing.') }
  }

  const title = wishlist ? 'My Wishlist' : 'My Listings'

  return (
    <section className="section collection-page">
      <div className="section-heading">
        <div>
          <span className="eyebrow">YOUR ACCOUNT</span>
          <h1>{title}</h1>
          <p>
            {wishlist
              ? 'Listings you have saved for later.'
              : 'Manage the items you have listed on ReUse Campus.'}
          </p>
        </div>
        <a href="/profile" className="text-link">← Back to Profile</a>
      </div>

      {loading && <p className="section-message">Loading listings...</p>}
      {error && <p className="section-message">{error}</p>}

      {!loading && !error && listings.length === 0 && (
        <div className="collection-empty">
          {wishlist ? <Heart size={36} /> : <Package size={36} />}
          <h2>{wishlist ? 'Your wishlist is empty' : 'You have no listings yet'}</h2>
          <p>
            {wishlist
              ? 'Save items you like by selecting the heart icon.'
              : 'Start sharing items with your campus community.'}
          </p>
          <a href={wishlist ? '/browse' : '/listings/new'} className="signup-button">
            {wishlist ? 'Explore listings' : 'Create a listing'}
          </a>
        </div>
      )}

      {!loading && listings.length > 0 && (
        <div className="product-grid">
          {listings.map((item) => (
            <article className="product-card" key={item.id}>
              <a href={`/listings/${item.id}`} className="product-image">
                {item.image_url ? (
                  <img src={item.image_url} alt={item.title} />
                ) : (
                  <Package className="product-placeholder-icon" />
                )}
                <span className="condition-tag">{item.condition}</span>
              </a>

              <div className="product-info">
                <div className="product-title-row">
                  <h3>{item.title}</h3>
                  {wishlist && (
                    <button
                      type="button"
                      className="icon-button favourite-active"
                      aria-label="Remove from wishlist"
                      onClick={() => removeFavourite(item.id)}
                    >
                      <Heart size={19} fill="currentColor" />
                    </button>
                  )}
                </div>
                <strong className="product-price">
                  ₹{Number(item.price || 0).toLocaleString('en-IN')}
                </strong>
                <a href={`/listings/${item.id}`} className="product-link">
                  View details →
                </a>
                {!wishlist && item.status !== 'reserved' && item.status !== 'sold' && (
                  <button type="button" className="danger-button" onClick={() => deleteListing(item.id)}>Delete listing</button>
                )}
                {!wishlist && <div className="seller-shortcuts"><a href="/enquiries">Enquiries</a><a href="/orders">Reservations</a></div>}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
