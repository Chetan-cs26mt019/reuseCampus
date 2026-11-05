import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'
import Hero from './components/home/Hero'
import CategorySection from './components/home/CategorySection'
import TrendingSection from './components/home/TrendingSection'
import Marketplace from './pages/Marketplace'
import Login from './pages/Login'
import Register from './pages/Register'
import ListingDetails from './pages/ListingDetails'
import CreateListing from './pages/CreateListing'
import './App.css'
import './pages/pages.css'

function App() {
  const path = window.location.pathname
  const listingMatch = path.match(/^\/listings\/(\d+)$/)

  let page

  if (path === '/browse') page = <Marketplace />
  else if (path === '/login') page = <Login />
  else if (path === '/signup') page = <Register />
  else if (path === '/listings/new') page = <CreateListing />
  else if (listingMatch) page = <ListingDetails listingId={listingMatch[1]} />
  else page = (
    <>
      <Hero />
      <CategorySection />
      <TrendingSection />
    </>
  )

  return (
    <>
      <Navbar />
      <main>{page}</main>
      <Footer />
    </>
  )
}

export default App
