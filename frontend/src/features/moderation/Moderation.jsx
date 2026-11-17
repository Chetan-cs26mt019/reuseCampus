import { useCallback, useEffect, useState } from 'react'
import { apiRequest } from '../../services/api'

const actionLabels = {
  hide_listing: 'Listing hidden',
  unhide_listing: 'Listing unhidden',
  remove_listing: 'Listing permanently removed',
  dismiss: 'Report dismissed',
  close_report: 'Report closed',
}

export default function Moderation() {
  const [reports, setReports] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busyReport, setBusyReport] = useState(null)

  const loadReports = useCallback(async () => {
    try {
      setError('')
      const data = await apiRequest('/moderation/reports')
      setReports(data.items || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = setTimeout(loadReports, 0)
    return () => clearTimeout(timer)
  }, [loadReports])

  async function perform(report, endpoint, payload, confirmation) {
    if (confirmation && !window.confirm(confirmation)) return
    const reason = window.prompt('Enter the reason for this moderation change (at least 3 characters):')
    if (!reason || reason.trim().length < 3) return

    setBusyReport(report.id)
    setError('')
    try {
      await apiRequest(endpoint(report.id), {
        method: 'PATCH',
        body: JSON.stringify({ ...payload, reason: reason.trim() }),
      })
      await loadReports()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyReport(null)
    }
  }

  function review(report, action) {
    const warning = action === 'remove_listing'
      ? 'This permanently removes the listing. It cannot be restored later. Continue?'
      : null
    return perform(
      report,
      (id) => `/moderation/reports/${id}`,
      { action },
      warning,
    )
  }

  function close(report) {
    return perform(
      report,
      (id) => `/moderation/reports/${id}/close`,
      {},
      'Close this report? Its moderation decision will become read-only.',
    )
  }

  return (
    <section className="section page-section">
      <h2>Reports and Moderation</h2>
      <p>Review reported products, revise decisions while reports are open for moderation, and close completed reports.</p>
      {error && <p className="form-error">{error}</p>}
      <h3>Moderation reports</h3>
      {loading ? <p>Loading reports...</p> : reports.length === 0 ? (
        <p className="section-message">There are no reports to review.</p>
      ) : reports.map((report) => {
        const isClosed = report.status === 'closed'
        const isRemoved = Boolean(report.listing_removed || report.listing_status === 'removed')
        const latestAction = report.actions?.[report.actions.length - 1]?.action
        const canUnhide = !isRemoved && report.listing_hidden && latestAction === 'hide_listing'
        const canHide = !isRemoved && !report.listing_hidden && report.listing_status !== 'sold'
        const canRemove = !isRemoved
        const canDismiss = !isRemoved

        return (
          <article className="feature-card moderation-report-card" key={report.id}>
            <div className="reservation-product">
              {report.listing_image
                ? <img src={report.listing_image} alt={report.listing_title || 'Reported product'} />
                : <span className="product-thumb-placeholder">📦</span>}
              <div>
                <strong>{report.listing_title || `Listing #${report.listing_id}`}</strong>
                <p>
                  {report.listing_price != null ? `₹${Number(report.listing_price).toLocaleString('en-IN')} · ` : ''}
                  {report.listing_condition || 'Condition not provided'} · Listing status: {report.listing_status || 'Unknown'}
                </p>
                <p>{report.listing_hidden ? 'Currently hidden' : report.listing_removed ? 'Permanently removed' : 'Not hidden'}</p>
                <a href={`/listings/${report.listing_id}`} target="_blank" rel="noreferrer">View reported product</a>
              </div>
            </div>
            <div className="moderation-report-meta">
              <strong>Report #{report.id}</strong>
              <span className={`moderation-status moderation-status-${report.status}`}>{report.status.replaceAll('_', ' ')}</span>
            </div>
            <p><strong>Reason:</strong> {report.reason.replaceAll('_', ' ')}</p>
            <p><strong>Details:</strong> {report.details || 'No additional details provided.'}</p>
            <p><strong>Reporter ID:</strong> {report.reporter_id}</p>
            <p><strong>Submitted:</strong> {new Date(report.created_at).toLocaleString()}</p>
            {report.reviewed_at && <p><strong>Last reviewed:</strong> {new Date(report.reviewed_at).toLocaleString()}</p>}
            {report.closed_at && <p><strong>Closed:</strong> {new Date(report.closed_at).toLocaleString()} · Moderator #{report.closed_by}</p>}

            {!isClosed && !isRemoved && (
              <div className="moderation-decision-panel">
                <strong>{report.status === 'open' ? 'Review report' : 'Change moderation decision'}</strong>
                <div className="feature-actions">
                  {canHide && <button disabled={busyReport === report.id} onClick={() => review(report, 'hide_listing')}>Hide listing</button>}
                  {canUnhide && <button disabled={busyReport === report.id} onClick={() => review(report, 'unhide_listing')}>Unhide listing</button>}
                  {canRemove && <button className="moderation-danger-button" disabled={busyReport === report.id} onClick={() => review(report, 'remove_listing')}>Permanently remove</button>}
                  {canDismiss && <button disabled={busyReport === report.id} onClick={() => review(report, 'dismiss')}>Dismiss report</button>}
                </div>
              </div>
            )}
            {isRemoved && !isClosed && (
              <p className="section-message">This listing was permanently removed. Its removal cannot be reversed; you can close the report when review is complete.</p>
            )}
            {!isClosed && ['action_taken', 'dismissed'].includes(report.status) && (
              <div className="feature-actions">
                <button disabled={busyReport === report.id} onClick={() => close(report)}>Close report</button>
              </div>
            )}
            {isClosed && <p className="section-message">This report is closed and read-only. No further moderation action is available.</p>}

            <div className="moderation-history">
              <strong>Action history</strong>
              {report.actions?.length ? (
                <ol>
                  {report.actions.map((entry) => (
                    <li key={entry.id}>
                      <strong>{actionLabels[entry.action] || entry.action.replaceAll('_', ' ')}</strong>
                      <span> · Moderator #{entry.moderator_id} · {new Date(entry.created_at).toLocaleString()}</span>
                      {entry.reason && <p>{entry.reason}</p>}
                    </li>
                  ))}
                </ol>
              ) : <p>No moderation actions have been recorded yet.</p>}
            </div>
          </article>
        )
      })}
    </section>
  )
}
