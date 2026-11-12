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
import Profile from './pages/Profile'
import ListingCollection from './pages/ListingCollection'

import Reservations from './features/reservations/Reservations'
import Enquiries from './features/enquiries/Enquiries'
import Moderation from './features/moderation/Moderation'
import Recommendations from './features/recommendations/Recommendations'

import './App.css'
import './pages/pages.css'
import './features/features.css'

function App() {
  const path = window.location.pathname
  const listingMatch = path.match(/^\/listings\/(\d+)$/)

  let page

  if (path === '/browse') page = <Marketplace />
  else if (path === '/login') page = <Login />
  else if (path === '/profile') page = <Profile />
  else if (path === '/my-listings') page = <ListingCollection />
  else if (path === '/wishlist') page = <ListingCollection wishlist />
  else if (path === '/signup') page = <Register />
  else if (path === '/listings/new') page = <CreateListing />
  else if (path === '/orders') page = <Reservations />
  else if (path === '/enquiries') page = <Enquiries />
  else if (path === '/moderation') page = <Moderation />
  else if (path === '/recommendations') page = <Recommendations />
  else if (listingMatch) {
    page = <ListingDetails listingId={listingMatch[1]} />
  } else {
    page = (
      <>
        <Hero />
        <CategorySection />
        <TrendingSection />
      </>
    )
  }

  return (
    <>
      <Navbar />
      <main>{page}</main>
      <Footer />
    </>
  )
}

export default App
