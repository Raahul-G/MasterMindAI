import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import StreakCounter from '../components/StreakCounter'
import LoadingSpinner from '../components/LoadingSpinner'
import { getModules, getModule } from '../api/modules'
import { getStreak } from '../api/gamification'
import { getMe } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import { useLearningStore } from '../store/learningStore'
import type { Module, Streak } from '../types'

const LEVEL_LABELS = { kid: 'Kid', intermediate: 'Intermediate', expert: 'Expert' }
const LEVEL_COLORS = {
  kid: 'bg-green-100 text-green-700',
  intermediate: 'bg-blue-100 text-blue-700',
  expert: 'bg-purple-100 text-purple-700',
}

export default function Dashboard() {
  const [modules, setModules] = useState<Module[]>([])
  const [streak, setStreak] = useState<Streak | null>(null)
  const [loading, setLoading] = useState(true)
  const { user, setAuth, token } = useAuthStore()
  const setModule = useLearningStore((s) => s.setModule)
  const navigate = useNavigate()

  const handleContinue = async (mod: Module) => {
    try {
      const { data } = await getModule(mod.id)
      setModule(data.id.toString(), data.topic, data.level, data.eli5_text ?? '', data.passages)
      navigate('/learn')
    } catch {
      navigate('/learn/start')
    }
  }

  useEffect(() => {
    const load = async () => {
      try {
        const [modsRes, streakRes] = await Promise.all([getModules(), getStreak()])
        setModules(modsRes.data)
        setStreak(streakRes.data)
        if (!user && token) {
          const { data: me } = await getMe()
          setAuth(token, me)
        }
      } catch {
        // token expired — let ProtectedRoute handle
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <>
      <Navbar />
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Welcome back{user ? `, ${user.full_name.split(' ')[0]}` : ''}!
            </h1>
            <p className="text-gray-400 text-sm mt-1">Pick up where you left off or start something new.</p>
          </div>
          {streak && <StreakCounter current={streak.current_streak} longest={streak.longest_streak} />}
        </div>

        <button
          onClick={() => navigate('/learn/start')}
          className="w-full bg-indigo-600 text-white font-semibold py-4 rounded-2xl hover:bg-indigo-700 transition-colors text-lg mb-8 flex items-center justify-center gap-2"
        >
          <span>+</span> Start New Module
        </button>

        {loading ? (
          <LoadingSpinner />
        ) : modules.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">📚</div>
            <h2 className="text-xl font-semibold text-gray-700 mb-2">No modules yet</h2>
            <p className="text-gray-400">Start your first module above and begin learning.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {modules.map((mod) => (
              <div
                key={mod.id}
                className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${LEVEL_COLORS[mod.level]}`}>
                      {LEVEL_LABELS[mod.level]}
                    </span>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      mod.status === 'completed' ? 'bg-green-50 text-green-600' : 'bg-yellow-50 text-yellow-600'
                    }`}>
                      {mod.status === 'completed' ? 'Completed' : 'In Progress'}
                    </span>
                  </div>
                  <h3 className="font-semibold text-gray-900">{mod.topic}</h3>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(mod.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() =>
                    mod.status === 'completed'
                      ? navigate(`/modules/${mod.id}/review`)
                      : handleContinue(mod)
                  }
                  className="text-sm text-indigo-600 font-medium hover:underline"
                >
                  {mod.status === 'completed' ? 'Review' : 'Continue'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}
