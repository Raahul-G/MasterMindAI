import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import StreakCounter from '../components/StreakCounter'
import LoadingSpinner from '../components/LoadingSpinner'
import { getModules } from '../api/modules'
import { resumeModule } from '../api/learning'
import { getStreak } from '../api/gamification'
import { getMe } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import { useLearningStore } from '../store/learningStore'
import type { Module, Streak } from '../types'

const LEVEL_LABELS: Record<string, string> = { kid: 'Kid', intermediate: 'Intermediate', expert: 'Expert' }
const LEVEL_COLORS: Record<string, string> = {
  kid: 'bg-green-100 text-forest-900',
  intermediate: 'bg-green-600 text-white',
  expert: 'bg-purple-100 text-purple-600',
}

export default function Dashboard() {
  const [modules, setModules] = useState<Module[]>([])
  const [streak, setStreak] = useState<Streak | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingModuleId, setLoadingModuleId] = useState<string | null>(null)
  const [errorModuleId, setErrorModuleId] = useState<string | null>(null)
  const { user, setAuth, token, refreshToken } = useAuthStore()
  const setStart = useLearningStore((s) => s.setStart)
  const navigate = useNavigate()

  const handleContinue = async (mod: Module) => {
    setLoadingModuleId(mod.id)
    setErrorModuleId(null)
    try {
      const { data } = await resumeModule(mod.id)
      setStart(data)
      navigate('/learn')
    } catch {
      setErrorModuleId(mod.id)
    } finally {
      setLoadingModuleId(null)
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
          setAuth(token, refreshToken ?? '', me)
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
            <h1 className="text-2xl font-bold text-forest-900">
              Welcome back{user ? `, ${user.full_name?.split(' ')[0] ?? 'there'}` : ''}!
            </h1>
            <p className="text-gray-400 text-sm mt-1">Pick up where you left off or start something new.</p>
          </div>
          {streak && <StreakCounter current={streak.current_streak} longest={streak.longest_streak} />}
        </div>

        <button
          onClick={() => navigate('/learn/start')}
          className="w-full bg-green-600 text-white font-extrabold py-4 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight text-lg mb-8 flex items-center justify-center gap-2"
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
              <div key={mod.id}>
                <div className="bg-white border-2 border-gray-200 rounded-2xl p-5 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${LEVEL_COLORS[mod.level]}`}>
                        {LEVEL_LABELS[mod.level]}
                      </span>
                      <span className="text-xs font-semibold text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                        {mod.concepts_learned} concept{mod.concepts_learned !== 1 ? 's' : ''} learned
                      </span>
                    </div>
                    <h3 className="font-semibold text-forest-900">{mod.topic}</h3>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {new Date(mod.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => navigate(`/modules/${mod.id}/review`)}
                      className="text-sm text-gray-400 font-medium hover:underline"
                    >
                      Review
                    </button>
                    <button
                      onClick={() => handleContinue(mod)}
                      disabled={loadingModuleId !== null}
                      className="text-sm text-green-600 font-medium hover:underline disabled:opacity-40"
                    >
                      {loadingModuleId === mod.id ? 'Loading...' : 'Continue'}
                    </button>
                  </div>
                </div>
                {errorModuleId === mod.id && (
                  <p className="text-xs text-red-500 mt-2 px-1">
                    Couldn't resume — please try again.
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}
