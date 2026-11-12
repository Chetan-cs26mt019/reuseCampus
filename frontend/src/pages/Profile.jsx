import { apiRequest } from '../services/api'
import {
  UserRound,
  Package,
  Heart,
  ClipboardList,
  MessageCircle,
  Sparkles,
  ShieldCheck,
  LogOut,
  Trash2,
} from 'lucide-react'

function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem('current_user') || 'null')
  } catch {
    return null
  }
}

export default function Profile() {
  const user = getCurrentUser()

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('current_user')
    window.location.assign('/')
  }

  async function deleteAccount() {
    const password = window.prompt('Enter your password to permanently deactivate and anonymise your account:')
    if (!password) return
    if (!window.confirm('Are you sure? Your account will be deactivated and your listings removed.')) return
    try {
      await apiRequest('/auth/me', { method: 'DELETE', body: JSON.stringify({ password }) })
      localStorage.removeItem('access_token')
      localStorage.removeItem('current_user')
      window.location.assign('/')
    } catch (err) { window.alert(err.message || 'Unable to delete account.') }
  }

  const sections = [
    {
      title: 'My Listings',
      description: 'Manage items you have listed for sale.',
      icon: Package,
      link: '/my-listings',
    },
    {
      title: 'Wishlist',
      description: 'Find the items you have saved.',
      icon: Heart,
      link: '/wishlist',
    },
    {
      title: 'My Reservations',
      description: 'View and manage your reservations.',
      icon: ClipboardList,
      link: '/orders',
    },
    {
      title: 'Messages',
      description: 'View your conversations and enquiries.',
      icon: MessageCircle,
      link: '/enquiries',
    },
    {
      title: 'Recommendations',
      description: 'Explore recommendations for you.',
      icon: Sparkles,
      link: '/recommendations',
    },
  ]

  if (user?.role === 'moderator') {
    sections.push({
      title: 'Moderation',
      description: 'Review and manage reported listings.',
      icon: ShieldCheck,
      link: '/moderation',
    })
  }

  return (
    <section className="profile-page">
      <div className="profile-header">
        <div className="profile-avatar">
          <UserRound size={34} />
        </div>
        <div>
          <span className="profile-eyebrow">MY ACCOUNT</span>
          <h1>{user?.username || user?.full_name || 'Welcome to ReUse Campus'}</h1>
          <p>{user?.email || 'Manage your marketplace activities'}</p>
        </div>
      </div>

      <div className="profile-section-heading">
        <h2>Your Dashboard</h2>
        <p>Manage your account and marketplace activities.</p>
      </div>

      <div className="profile-grid">
        {sections.map(({ title, description, icon: Icon, link }) => (
          <a href={link} className="profile-card" key={title}>
            <span className="profile-card-icon">
              <Icon size={23} />
            </span>
            <h3>{title}</h3>
            <p>{description}</p>
            <span className="profile-card-link">Open →</span>
          </a>
        ))}
      </div>

      <div className="profile-account-actions">
        <button className="profile-logout" onClick={logout}>
          <LogOut size={18} /> Logout
        </button>
        <button className="profile-delete" onClick={deleteAccount}>
          <Trash2 size={18} /> Delete account
        </button>
      </div>
    </section>
  )
}
