import { useState } from 'react'
import { apiRequest } from '../services/api'

export default function Login() {
  const [form, setForm] = useState({ username_or_email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      const result = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      localStorage.setItem('access_token', result.access_token)
      localStorage.setItem('current_user', JSON.stringify(result.user))
      window.location.href = '/browse'
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="form-page">
      <form className="app-form" onSubmit={submit}>
        <h2>Welcome back</h2>
        <label>Username or email
          <input required value={form.username_or_email}
            onChange={(e) => setForm({ ...form, username_or_email: e.target.value })} />
        </label>
        <label>Password
          <input required type="password" value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </label>
        {error && <p className="form-error">{error}</p>}
        <button disabled={loading}>{loading ? 'Signing in...' : 'Login'}</button>
        <p>New here? <a href="/signup">Create an account</a></p>
      </form>
    </section>
  )
}
