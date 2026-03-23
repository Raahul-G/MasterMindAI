import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import AchievementBadge from '../components/AchievementBadge'
import { exportDownload } from '../api/modules'
import { getAchievements } from '../api/gamification'
import { useLearningStore } from '../store/learningStore'
import { useEffect } from 'react'
import type { Achievement } from '../types'

export default function ModuleComplete() {
  const { moduleId, topic, level, quizResult, reset } = useLearningStore()
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [downloading, setDownloading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    getAchievements().then((res) => setAchievements(res.data)).catch(() => {})
  }, [])

  if (!moduleId || !quizResult) {
    navigate('/dashboard')
    return null
  }

  const handleDownload = async () => {
    setDownloading(true)
    try {
      const { data } = await exportDownload(moduleId)
      window.open(data.download_url, '_blank')
    } finally {
      setDownloading(false)
    }
  }

  const handleBackToDashboard = () => {
    reset()
    navigate('/dashboard')
  }

  return (
    <>
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-12 text-center">
        <div className="text-6xl mb-4">🏆</div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Module Complete!</h1>
        <p className="text-gray-400 mb-8">You mastered <span className="font-semibold text-gray-700">{topic}</span></p>

        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-indigo-50 rounded-2xl p-4">
            <p className="text-2xl font-bold text-indigo-600">{quizResult.score}/{quizResult.total}</p>
            <p className="text-xs text-gray-400 mt-1">Final Score</p>
          </div>
          <div className="bg-green-50 rounded-2xl p-4">
            <p className="text-2xl font-bold text-green-600 capitalize">{level}</p>
            <p className="text-xs text-gray-400 mt-1">Level</p>
          </div>
          <div className="bg-orange-50 rounded-2xl p-4">
            <p className="text-2xl font-bold text-orange-600">🔥</p>
            <p className="text-xs text-gray-400 mt-1">Streak Updated</p>
          </div>
        </div>

        {achievements.length > 0 && (
          <div className="text-left mb-8">
            <p className="text-sm font-semibold text-gray-700 mb-3">Achievements Earned</p>
            <div className="flex flex-col gap-2">
              {achievements.map((a) => (
                <AchievementBadge key={a.slug} emoji={a.icon_emoji} name={a.name} description={a.description} />
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-col gap-3">
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="w-full bg-white border-2 border-indigo-200 text-indigo-600 font-semibold py-3 rounded-xl hover:border-indigo-400 transition-colors disabled:opacity-50"
          >
            {downloading ? 'Preparing download...' : 'Download Markdown Summary'}
          </button>
          <button
            onClick={handleBackToDashboard}
            className="w-full bg-indigo-600 text-white font-semibold py-4 rounded-xl hover:bg-indigo-700 transition-colors text-lg"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    </>
  )
}
