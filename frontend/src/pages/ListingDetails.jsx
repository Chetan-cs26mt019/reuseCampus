import { useEffect, useState } from 'react'
import { apiGet, apiRequest, getItems } from '../services/api'

export default function ListingDetails({ listingId }) {
  const [listing, setListing] = useState(null)
  const [images, setImages] = useState([])
  const [error, setError] = useState('')
  const [reportReason, setReportReason] = useState('spam')
  const [reportDetails, setReportDetails] = useState('')
  const [notice, setNotice] = useState('')
  const user = (() => { try { return JSON.parse(localStorage.getItem('current_user') || 'null') } catch { return null } })()
  const isOwner = Boolean(user && listing && Number(user.id) === Number(listing.seller_id))

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
      window.location.assign('/enquiries')
    } catch (err) {
      setError(err.message)
    }
  }

  async function reserve() {
    try {
      await apiRequest('/orders', { method: 'POST', body: JSON.stringify({ listing_id: Number(listingId) }) })
      setNotice('Reservation request sent. You can track it in My Reservations.')
    } catch (err) { setError(err.message) }
  }

  async function reportListing(event) {
    event.preventDefault()
    try {
      await apiRequest(`/listings/${listingId}/reports`, {
        method: 'POST',
        body: JSON.stringify({ reason: reportReason, details: reportDetails || null }),
      })
      setNotice('Thank you. Your report has been submitted for moderator review.')
      setReportDetails('')
    } catch (err) { setError(err.message) }
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
          {isOwner ? (
            <div className="seller-tools">
              <strong>This is your listing.</strong>
              <a className="signup-button" href="/my-listings">Manage my listings</a>
              <a className="text-link" href="/enquiries">Check enquiries</a>
              <a className="text-link" href="/orders">Check reservations</a>
            </div>
          ) : (
            <div className="detail-actions">
              <button onClick={enquire}>Contact seller</button>
              {user && <button type="button" onClick={reserve}>Request reservation</button>}
            </div>
          )}
          {user && !isOwner && (
            <form className="report-form" onSubmit={reportListing}>
              <h3>Report this listing</h3>
              <select value={reportReason} onChange={(e) => setReportReason(e.target.value)}>
                {['spam', 'fraud', 'prohibited_item', 'misleading_listing', 'harassment', 'other'].map((reason) => <option key={reason} value={reason}>{reason.replaceAll('_', ' ')}</option>)}
              </select>
              <textarea maxLength="2000" placeholder="Add details (optional)" value={reportDetails} onChange={(e) => setReportDetails(e.target.value)} />
              <button type="submit">Submit report</button>
            </form>
          )}
          {notice && <p className="section-message">{notice}</p>}
          <p><a href="/browse">← Back to marketplace</a></p>
        </div>
      </div>
    </section>
  )
}
