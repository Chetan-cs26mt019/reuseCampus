import { ShoppingBag } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-brand">
          <a href="/" className="brand">
            <span className="brand-icon"><ShoppingBag size={22} /></span>
            <span>ReUse<span className="brand-highlight">Campus</span></span>
          </a>
          <p>
            A student-powered marketplace to buy, sell and reuse
            useful items within the campus community.
          </p>
        </div>

        <div className="footer-column">
          <h4>Marketplace</h4>
          <a href="/browse">Browse products</a>
          <a href="/#categories">Explore categories</a>
          <a href="/#trending">Popular products</a>
          <a href="/listings/new">Sell an item</a>
        </div>

        <div className="footer-column">
          <h4>My Account</h4>
          <a href="/profile">My profile</a>
          <a href="/my-listings">My listings</a>
          <a href="/wishlist">My wishlist</a>
          <a href="/orders">My orders</a>
          <a href="/enquiries">My enquiries</a>
        </div>

        <div className="footer-column">
          <h4>Discover</h4>
          <a href="/recommendations">Recommendations</a>
          <a href="/login">Sign in</a>
          <a href="/signup">Create account</a>
        </div>
      </div>

      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} ReUse Campus. All rights reserved.</span>
        <span>Reuse more. Waste less. 🌱</span>
      </div>
    </footer>
  )
}
