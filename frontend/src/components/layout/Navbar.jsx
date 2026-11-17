import { useState } from 'react'
import { ShoppingBag, Menu, X, UserRound } from 'lucide-react'

function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem('current_user') || 'null')
  } catch {
    return null
  }
}

function isActivePath(pathname, href) {
  if (href === '/') return pathname === '/'
  if (href === '/browse') {
    return pathname === '/browse' || /^\/listings\/\d+$/.test(pathname)
  }
  return pathname === href || pathname.startsWith(`${href}/`)
}

export default function Navbar() {
  const currentUser = getCurrentUser()
  const pathname = window.location.pathname
  const [menuOpen, setMenuOpen] = useState(false)

  function closeMenu() {
    setMenuOpen(false)
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

        <nav
          className={`nav-links ${menuOpen ? 'nav-open' : ''}`}
          aria-label="Main navigation"
        >
          <a
            href="/"
            className={isActivePath(pathname, '/') ? 'active' : undefined}
            aria-current={isActivePath(pathname, '/') ? 'page' : undefined}
            onClick={closeMenu}
          >
            Home
          </a>

          <a
            href="/browse"
            className={isActivePath(pathname, '/browse') ? 'active' : undefined}
            aria-current={isActivePath(pathname, '/browse') ? 'page' : undefined}
            onClick={closeMenu}
          >
            Browse
          </a>

          <a
            href="/listings/new"
            className={isActivePath(pathname, '/listings/new') ? 'active' : undefined}
            aria-current={isActivePath(pathname, '/listings/new') ? 'page' : undefined}
            onClick={closeMenu}
          >
            Sell an Item
          </a>

          <a
            href="/recommendations"
            className={isActivePath(pathname, '/recommendations') ? 'active' : undefined}
            aria-current={isActivePath(pathname, '/recommendations') ? 'page' : undefined}
            onClick={closeMenu}
          >
            Recommendations
          </a>

          {currentUser?.role === 'moderator' && (
            <a
              href="/moderation"
              className={isActivePath(pathname, '/moderation') ? 'active' : undefined}
              aria-current={isActivePath(pathname, '/moderation') ? 'page' : undefined}
              onClick={closeMenu}
            >
              Moderation
            </a>
          )}
        </nav>

        <div className="nav-actions">
          {currentUser ? (
            <a
              href="/profile"
              className={`login-link${isActivePath(pathname, '/profile') ? ' active' : ''}`}
              aria-current={isActivePath(pathname, '/profile') ? 'page' : undefined}
            >
              <UserRound size={19} />
              Profile
            </a>
          ) : (
            <>
              <a
                href="/login"
                className={`login-link${isActivePath(pathname, '/login') ? ' active' : ''}`}
                aria-current={isActivePath(pathname, '/login') ? 'page' : undefined}
              >
                <UserRound size={18} />
                Login
              </a>

              <a
                href="/signup"
                className={`signup-button${isActivePath(pathname, '/signup') ? ' active' : ''}`}
                aria-current={isActivePath(pathname, '/signup') ? 'page' : undefined}
              >
                Sign Up
              </a>
            </>
          )}
        </div>

        <button
          className="mobile-menu"
          onClick={() => setMenuOpen((open) => !open)}
          aria-label={menuOpen ? 'Close navigation' : 'Open navigation'}
          aria-expanded={menuOpen}
          aria-controls="main-navigation"
        >
          {menuOpen ? <X /> : <Menu />}
        </button>
      </div>
    </header>
  )
}
