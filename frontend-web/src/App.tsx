import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import TopicSelection from './pages/TopicSelection'
import Learning from './pages/Learning'
import Quiz from './pages/Quiz'
import QuizResults from './pages/QuizResults'
import Remediation from './pages/Remediation'
import ModuleComplete from './pages/ModuleComplete'
import Profile from './pages/Profile'
import Friends from './pages/Friends'
import ModuleReview from './pages/ModuleReview'

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
        <Route path="/quiz" element={<ProtectedRoute><Quiz /></ProtectedRoute>} />
        <Route path="/quiz/results" element={<ProtectedRoute><QuizResults /></ProtectedRoute>} />
        <Route path="/remediation" element={<ProtectedRoute><Remediation /></ProtectedRoute>} />
        <Route path="/complete" element={<ProtectedRoute><ModuleComplete /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="/friends" element={<ProtectedRoute><Friends /></ProtectedRoute>} />
        <Route path="/modules/:id/review" element={<ProtectedRoute><ModuleReview /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
