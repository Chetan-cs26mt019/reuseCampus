import { useState } from 'react'
import { apiRequest } from '../services/api'

const initialForm = {
  email: '',
  username: '',
  password: '',
  full_name: '',
  student_id: '',
}

export default function Register() {
  const [form, setForm] = useState(initialForm)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function submit(event) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      await apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ ...form, student_id: form.student_id || null }),
      })
      window.location.href = '/login'
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="form-page">
      <form className="app-form" onSubmit={submit}>
        <h2>Create your account</h2>
        <label>Full name
          <input required value={form.full_name} onChange={(e) => update('full_name', e.target.value)} />
        </label>
        <label>Email
          <input required type="email" value={form.email} onChange={(e) => update('email', e.target.value)} />
        </label>
        <label>Username
          <input required minLength="3" value={form.username} onChange={(e) => update('username', e.target.value)} />
        </label>
        <label>Student ID (optional)
          <input value={form.student_id} onChange={(e) => update('student_id', e.target.value)} />
        </label>
        <label>Password (minimum 12 characters)
          <input required type="password" minLength="12" value={form.password}
            onChange={(e) => update('password', e.target.value)} />
        </label>
        {error && <p className="form-error">{error}</p>}
        <button disabled={loading}>{loading ? 'Creating account...' : 'Register'}</button>
        <p>Already registered? <a href="/login">Login</a></p>
      </form>
    </section>
  )
}
