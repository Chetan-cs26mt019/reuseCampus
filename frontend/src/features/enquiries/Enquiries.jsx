import { useCallback, useEffect, useState } from 'react'
import { apiRequest } from '../../services/apiClient'

export default function Enquiries() {
  const [threads, setThreads] = useState([])
  const [selected, setSelected] = useState(null)
  const [messages, setMessages] = useState([])
  const [listingId, setListingId] = useState('')
  const [body, setBody] = useState('')
  const [error, setError] = useState('')

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

  async function createThread(event) {
    event.preventDefault()
    try {
      await apiRequest('/enquiry-threads', {
        method: 'POST',
        body: JSON.stringify({ listing_id: Number(listingId) }),
      })
      setListingId('')
      await loadThreads()
    } catch (err) {
      setError(err.message)
    }
  }

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
      <form className="feature-form" onSubmit={createThread}>
        <input type="number" min="1" required placeholder="Listing ID"
          value={listingId} onChange={(e) => setListingId(e.target.value)} />
        <button>Start enquiry</button>
      </form>
      {error && <p className="form-error">{error}</p>}
      <div className="messaging-layout">
        <div>
          <h3>Your conversations</h3>
          {threads.map((thread) => (
            <button className="thread-button" key={thread.id}
              onClick={() => openThread(thread)}>
              Listing #{thread.listing_id} · {thread.status}
            </button>
          ))}
        </div>
        <div className="message-panel">
          <h3>{selected ? `Conversation #${selected.id}` : 'Select a conversation'}</h3>
          {messages.map((message) => (
            <article className="message-item" key={message.id}>
              <small>Sender #{message.sender_id}</small>
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
