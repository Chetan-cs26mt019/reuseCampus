import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'
import Hero from './components/home/Hero'
import CategorySection from './components/home/CategorySection'
import TrendingSection from './components/home/TrendingSection'
import './App.css'

function App() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <CategorySection />
        <TrendingSection />
      </main>
      <Footer />
    </>
  )
}

export default App
