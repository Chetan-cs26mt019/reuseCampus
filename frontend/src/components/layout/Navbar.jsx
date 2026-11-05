import { useState } from 'react'
import {
  Search,
  ShoppingBag,
  Menu,
  X,
  UserRound,
} from 'lucide-react'

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [search, setSearch] = useState('')

  function handleSearch(event) {
    event.preventDefault()

    if (!search.trim()) return

    window.location.href = `/browse?q=${encodeURIComponent(search)}`
  }

  return (
    <header className="navbar">
      <div className="nav-container">
        <a href="/" className="brand">
          <span className="brand-icon">
            <ShoppingBag size={22} />
          </span>
          <span>ReUse<span className="brand-highlight">Campus</span></span>
        </a>

        <nav className={`nav-links ${menuOpen ? 'nav-open' : ''}`}>
          <a href="/">Home</a>
          <a href="/browse">Browse</a>
          <a href="#categories">Categories</a>
          <a href="#trending">Trending</a>
        </nav>

        <form className="nav-search" onSubmit={handleSearch}>
          <Search size={18} />
          <input
            type="search"
            placeholder="Search products..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </form>

        <div className="nav-actions">
          <a href="/login" className="login-link">
            <UserRound size={18} />
            Login
          </a>
          <a href="/signup" className="signup-button">
            Get Started
          </a>
        </div>

        <button
          className="mobile-menu"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle navigation"
        >
          {menuOpen ? <X /> : <Menu />}
        </button>
      </div>
    </header>
  )
}
