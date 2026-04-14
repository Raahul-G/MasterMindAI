import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import TopicSelection from './pages/TopicSelection'
import Learning from './pages/Learning'
import Profile from './pages/Profile'
import Friends from './pages/Friends'
import ModuleReview from './pages/ModuleReview'
import KnowledgeGraph from './pages/KnowledgeGraph'
import FriendGraph from './pages/FriendGraph'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/learn/start" element={<ProtectedRoute><TopicSelection /></ProtectedRoute>} />
        <Route path="/learn" element={<ProtectedRoute><Learning /></ProtectedRoute>} />
        <Route path="/quiz" element={<Navigate to="/dashboard" replace />} />
        <Route path="/quiz/results" element={<Navigate to="/dashboard" replace />} />
        <Route path="/remediation" element={<Navigate to="/dashboard" replace />} />
        <Route path="/complete" element={<Navigate to="/dashboard" replace />} />
        <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="/friends" element={<ProtectedRoute><Friends /></ProtectedRoute>} />
        <Route path="/modules/:id/review" element={<ProtectedRoute><ModuleReview /></ProtectedRoute>} />
        <Route path="/graph" element={<ProtectedRoute><KnowledgeGraph /></ProtectedRoute>} />
        <Route path="/graph/friend/:userId" element={<ProtectedRoute><FriendGraph /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
