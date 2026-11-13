import { useCallback, useEffect, useState } from 'react'
import { apiRequest } from '../../services/api'

export default function Enquiries() {
  const [threads, setThreads] = useState([])
  const [selected, setSelected] = useState(null)
  const [messages, setMessages] = useState([])
  const [body, setBody] = useState('')
  const [error, setError] = useState('')
  const user = (() => { try { return JSON.parse(localStorage.getItem('current_user') || 'null') } catch { return null } })()

  const loadThreads = useCallback(async () => {
    try {
      const data = await apiRequest('/enquiry-threads')
      setThreads(data.items || [])
    } catch (err) {
      setError(err.message)
    }
  }, [])

  async function openThread(thread) {
    setSelected(thread)
    try {
      const data = await apiRequest(`/enquiry-threads/${thread.id}/messages`)
      setMessages(data.items || [])
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => loadThreads(), 0)
    return () => clearTimeout(timer)
  }, [loadThreads])

  async function sendMessage(event) {
    event.preventDefault()
    if (!selected || !body.trim()) return

    try {
      await apiRequest(`/enquiry-threads/${selected.id}/messages`, {
        method: 'POST',
        body: JSON.stringify({ body: body.trim() }),
      })
      setBody('')
      await openThread(selected)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="section page-section">
      <h2>Enquiries and Messages</h2>
      <p className="section-message">Buyer enquiries and enquiries received about your listings appear here. Open a product page to start a new enquiry.</p>
      {error && <p className="form-error">{error}</p>}
      <div className="messaging-layout">
        <div>
          <h3>Your conversations</h3>
          {threads.map((thread) => (
            <button className="thread-button" key={thread.id}
              onClick={() => openThread(thread)}>
              <span className="thread-product">{thread.listing_image ? <img src={thread.listing_image} alt="" /> : <span className="product-thumb-placeholder">📦</span>}</span>
              <span><strong>{thread.listing_title || 'Product enquiry'}</strong><br /><small>{Number(thread.seller_id) === Number(user?.id) ? `Buyer: ${thread.buyer_name}` : `Seller: ${thread.seller_name}`} · {thread.status}</small></span>
            </button>
          ))}
        </div>
        <div className="message-panel">
          <h3>{selected ? selected.listing_title : 'Select a conversation'}</h3>{selected && <p className="section-message">{selected.listing_price != null ? `INR ${Number(selected.listing_price).toLocaleString('en-IN')} · ` : ''}{Number(selected.seller_id) === Number(user?.id) ? `Buyer: ${selected.buyer_name}` : `Seller: ${selected.seller_name}`}</p>}
          {messages.map((message) => (
            <article className="message-item" key={message.id}>
              <small>{message.sender_name || (Number(message.sender_id) === Number(user?.id) ? "You" : "Other participant")}</small>
              <p>{message.body}</p>
            </article>
          ))}
          {selected && (
            <form className="feature-form" onSubmit={sendMessage}>
              <input required maxLength="2000" value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Write a message..." />
              <button>Send</button>
            </form>
          )}
        </div>
      </div>
    </section>
  )
}
