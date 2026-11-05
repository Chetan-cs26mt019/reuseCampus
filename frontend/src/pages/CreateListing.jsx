import { useEffect, useState } from 'react'
import { apiGet, apiRequest, getItems } from '../services/api'

export default function CreateListing() {
  const [categories, setCategories] = useState([])
  const [form, setForm] = useState({
    category_id: '',
    title: '',
    description: '',
    price: '',
    condition: 'Good',
  })
  const [image, setImage] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    apiGet('/categories')
      .then((data) => setCategories(getItems(data)))
      .catch((err) => setError(err.message))
  }, [])

  async function submit(event) {
    event.preventDefault()
    setError('')

    try {
      const listing = await apiRequest('/listings', {
        method: 'POST',
        body: JSON.stringify({ ...form, category_id: Number(form.category_id), price: Number(form.price) }),
      })

      if (image) {
        const body = new FormData()
        body.append('file', image)
        await apiRequest(`/listings/${listing.id}/images`, {
          method: 'POST',
          body,
        })
      }

      window.location.href = `/listings/${listing.id}`
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="form-page">
      <form className="app-form" onSubmit={submit}>
        <h2>Create a listing</h2>
        <label>Category
          <select required value={form.category_id}
            onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
            <option value="">Choose category</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{category.name}</option>
            ))}
          </select>
        </label>
        <label>Title
          <input required minLength="3" value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </label>
        <label>Description
          <textarea required value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </label>
        <label>Price
          <input required type="number" min="0" step="0.01" value={form.price}
            onChange={(e) => setForm({ ...form, price: e.target.value })} />
        </label>
        <label>Condition
          <select value={form.condition}
            onChange={(e) => setForm({ ...form, condition: e.target.value })}>
            <option>New</option><option>Like New</option><option>Good</option><option>Fair</option>
          </select>
        </label>
        <label>Image (optional)
          <input type="file" accept="image/*" onChange={(e) => setImage(e.target.files[0])} />
        </label>
        {error && <p className="form-error">{error}</p>}
        <button type="submit">Publish listing</button>
      </form>
    </section>
  )
}
