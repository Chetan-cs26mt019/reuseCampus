import { useState } from 'react'
import { ShoppingBag, Menu, X, UserRound } from 'lucide-react'

function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem('current_user') || 'null')
  } catch {
    return null
  }
}

export default function Navbar() {
  const currentUser = getCurrentUser()
  const [menuOpen, setMenuOpen] = useState(false)

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
          <a href="/" onClick={() => setMenuOpen(false)}>Home</a>
          <a href="/browse" onClick={() => setMenuOpen(false)}>Browse</a>
          <a href="/listings/new" onClick={() => setMenuOpen(false)}>Sell an Item</a>
          <a href="/recommendations" onClick={() => setMenuOpen(false)}>Recommendations</a>

          {currentUser?.role === 'moderator' && (
            <a href="/moderation" onClick={() => setMenuOpen(false)}>Moderation</a>
          )}
        </nav>

        <div className="nav-actions">
          {currentUser ? (
            <a href="/profile" className="login-link">
              <UserRound size={19} />
              Profile
            </a>
          ) : (
            <>
              <a href="/login" className="login-link">
                <UserRound size={18} />
                Login
              </a>
              <a href="/signup" className="signup-button">
                Sign Up
              </a>
            </>
          )}
        </div>

        <button
          className="mobile-menu"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle navigation"
          aria-expanded={menuOpen}
        >
          {menuOpen ? <X /> : <Menu />}
        </button>
      </div>
    </header>
  )
}
