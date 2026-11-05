import { useEffect, useState } from 'react'
import { apiGet, apiRequest, getItems } from '../services/api'

export default function ListingDetails({ listingId }) {
  const [listing, setListing] = useState(null)
  const [images, setImages] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      apiGet(`/listings/${listingId}`),
      apiGet(`/listings/${listingId}/images`),
    ]).then(([item, imageData]) => {
      setListing(item)
      setImages(getItems(imageData))
    }).catch((err) => setError(err.message))
  }, [listingId])

  async function enquire() {
    try {
      await apiRequest('/enquiry-threads', {
        method: 'POST',
        body: JSON.stringify({ listing_id: Number(listingId) }),
      })
      window.location.href = '/enquiries'
    } catch (err) {
      setError(err.message)
    }
  }

  if (error) return <p className="section-message">{error}</p>
  if (!listing) return <p className="section-message">Loading listing...</p>

  return (
    <section className="section page-section">
      <div className="detail-layout">
        <div className="detail-images">
          {images.length ? images.map((image) => (
            <img key={image.id} src={image.image_url} alt={image.alt_text || listing.title} />
          )) : <div className="detail-placeholder">📦</div>}
        </div>
        <div className="detail-info">
          <span className="eyebrow">{listing.condition}</span>
          <h2>{listing.title}</h2>
          <strong className="product-price">
            {listing.currency || 'INR'} {Number(listing.price).toLocaleString('en-IN')}
          </strong>
          <p>{listing.description}</p>
          <p>Listing status: {listing.status}</p>
          <button onClick={enquire}>Contact seller</button>
          <p><a href="/browse">← Back to marketplace</a></p>
        </div>
      </div>
    </section>
  )
}
