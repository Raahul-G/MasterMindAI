import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function Navbar() {
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const logout = () => {
    clearAuth()
    navigate('/login')
  }

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <Link to="/dashboard" className="text-2xl text-purple-600" style={{ fontFamily: "'Righteous', cursive" }}>MasterMind AI 🧠</Link>
      {user && (
        <div className="flex items-center gap-4">
          <Link to="/dashboard" className="text-sm text-gray-500 hover:text-purple-600">🚀 Dashboard</Link>
          <Link to="/knowledge-map" className="text-sm text-gray-500 hover:text-purple-600">🗺️ Map</Link>
          <Link to="/friends" className="text-sm text-gray-500 hover:text-green-600">🫂 Friends</Link>
          <Link to="/profile" className="text-sm text-gray-600 hover:text-green-600">{user.full_name}</Link>
          <button onClick={logout} className="text-sm text-gray-400 hover:text-red-500">📤 Logout</button>
        </div>
      )}
    </nav>
  )
}
