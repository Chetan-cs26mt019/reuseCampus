import { ArrowRight, Sparkles } from 'lucide-react'

export default function Hero() {
  return (
    <section className="hero">
      <div className="hero-content">
        <div className="hero-badge">
          <Sparkles size={16} />
          <span>Campus Marketplace</span>
        </div>

        <h1>
          Give Your Things
          <br />
          <span>Another Life.</span>
        </h1>

        <p>
          Buy, sell and exchange pre-loved items with students
          on your campus. Save money, reduce waste and build
          a sustainable community.
        </p>

        <a className="hero-cta" href="/browse">
          View Products <ArrowRight size={18} />
        </a>

        <div className="hero-stats">
          <div><strong>Buy</strong><span>Affordable finds</span></div>
          <div><strong>Sell</strong><span>Earn from unused items</span></div>
          <div><strong>Reuse</strong><span>Make an impact</span></div>
        </div>
      </div>

      <div className="hero-visual">
        <div className="hero-circle">
          <span className="hero-emoji">♻️</span>
        </div>
        <div className="floating-card floating-card-one">
          <span>📚</span>
          <div><strong>Books</strong><small>Pass knowledge on</small></div>
        </div>
        <div className="floating-card floating-card-two">
          <span>💻</span>
          <div><strong>Electronics</strong><small>Reuse technology</small></div>
        </div>
        <div className="floating-card floating-card-three">
          <span>🎒</span>
          <div><strong>Campus essentials</strong><small>Find your next favourite</small></div>
        </div>
      </div>
    </section>
  )
}
