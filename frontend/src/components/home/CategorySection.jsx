import { useEffect, useState } from 'react'
import {
  BookOpen,
  Laptop,
  Armchair,
  Shirt,
  Dumbbell,
  Package,
} from 'lucide-react'
import { apiGet, getItems } from '../../services/api'

const icons = [BookOpen, Laptop, Armchair, Shirt, Dumbbell, Package]

const fallbackCategories = [
  { id: 1, name: 'Books' },
  { id: 2, name: 'Electronics' },
  { id: 3, name: 'Furniture' },
  { id: 4, name: 'Clothing' },
  { id: 5, name: 'Sports' },
  { id: 6, name: 'Others' },
]

export default function CategorySection() {
  const [categories, setCategories] = useState(fallbackCategories)

  useEffect(() => {
    apiGet('/categories')
      .then((data) => {
        const items = getItems(data)
        if (items.length) setCategories(items)
      })
      .catch((error) => console.error('Categories:', error))
  }, [])

  return (
    <section className="section" id="categories">
      <div className="section-heading">
        <div>
          <span className="eyebrow">EXPLORE CAMPUS</span>
          <h2>Browse by Category</h2>
          <p>Find exactly what you need for campus life.</p>
        </div>
        <a href="/browse" className="text-link">View all →</a>
      </div>

      <div className="category-grid">
        {categories.map((category, index) => {
          const Icon = icons[index % icons.length]

          return (
            <a
              className="category-card"
              href={`/browse?category=${category.id}`}
              key={category.id}
            >
              <span className={`category-icon category-${index % 6}`}>
                <Icon size={27} />
              </span>
              <h3>{category.name}</h3>
              <span className="category-arrow">Explore →</span>
            </a>
          )
        })}
      </div>
    </section>
  )
}
