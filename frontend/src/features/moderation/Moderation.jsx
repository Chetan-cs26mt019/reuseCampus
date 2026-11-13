import { useCallback, useEffect, useState } from 'react'
import { apiRequest } from '../../services/api'

const reasons = [
  'spam', 'fraud', 'prohibited_item',
  'misleading_listing', 'harassment', 'other',
]

export default function Moderation() {
  const [listingId, setListingId] = useState('')
  const [reason, setReason] = useState('spam')
  const [details, setDetails] = useState('')
  const [reports, setReports] = useState([])
  const [error, setError] = useState('')

  const loadReports = useCallback(async () => {
    try {
      const data = await apiRequest('/moderation/reports')
      setReports(data.items || [])
    } catch (err) {
      setError(err.message)
    }
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => loadReports(), 0)
    return () => clearTimeout(timer)
  }, [loadReports])

  async function submitReport(event) {
    event.preventDefault()
    try {
      await apiRequest(`/listings/${listingId}/reports`, {
        method: 'POST',
        body: JSON.stringify({ reason, details: details || null }),
      })
      setListingId('')
      setDetails('')
      setError('Report submitted successfully.')
    } catch (err) {
      setError(err.message)
    }
  }

  async function review(id, action) {
    const reviewReason = window.prompt('Enter a review reason (at least 3 characters):')
    if (!reviewReason || reviewReason.trim().length < 3) return

    try {
      await apiRequest(`/moderation/reports/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ action, reason: reviewReason.trim() }),
      })
      await loadReports()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="section page-section">
      <h2>Reports and Moderation</h2>
      <form className="feature-form" onSubmit={submitReport}>
        <input type="number" min="1" required placeholder="Listing ID"
          value={listingId} onChange={(e) => setListingId(e.target.value)} />
        <select value={reason} onChange={(e) => setReason(e.target.value)}>
          {reasons.map((value) => <option key={value}>{value}</option>)}
        </select>
        <input maxLength="2000" placeholder="Additional details"
          value={details} onChange={(e) => setDetails(e.target.value)} />
        <button>Submit report</button>
      </form>
      {error && <p>{error}</p>}
      <h3>Moderation reports</h3>
      {reports.map((report) => (
        <article className="feature-card" key={report.id}>
          <strong>Report #{report.id}</strong>
          <p>Listing #{report.listing_id} · {report.reason} · {report.status}</p>
          <p>{report.details}</p>
          <div className="feature-actions">
            {['dismiss', 'hide_listing', 'remove_listing'].map((action) => (
              <button key={action} onClick={() => review(report.id, action)}>
                {action.replaceAll('_', ' ')}
              </button>
            ))}
          </div>
        </article>
      ))}
      <p className="section-message">
        Audit history is recorded by the backend when a report is reviewed.
        A read endpoint for audit history is not currently exposed.
      </p>
    </section>
  )
}
