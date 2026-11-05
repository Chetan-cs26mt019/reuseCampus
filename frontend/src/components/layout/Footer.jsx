import { ShoppingBag, Mail } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-brand">
          <a href="/" className="brand">
            <span className="brand-icon"><ShoppingBag size={22} /></span>
            <span>ReUse<span className="brand-highlight">Campus</span></span>
          </a>
          <p>A smarter, more sustainable marketplace for campus communities.</p>
        </div>

        <div className="footer-column">
          <h4>Marketplace</h4>
          <a href="/browse">Browse products</a>
          <a href="#categories">Categories</a>
          <a href="#trending">Trending items</a>
        </div>

        <div className="footer-column">
          <h4>Community</h4>
          <a href="/recommendations">Recommendations</a>
          <a href="/login">My account</a>
          <a href="/signup">Join us</a>
        </div>

        <div className="footer-column">
          <h4>Connect</h4>
          <a href="mailto:support@reusecampus.example">
            <Mail size={16} /> Email us
          </a>
        </div>
      </div>

      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} ReUseCampus. All rights reserved.</span>
        <span>Reuse more. Waste less. 🌱</span>
      </div>
    </footer>
  )
}
