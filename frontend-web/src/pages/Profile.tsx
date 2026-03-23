import { useEffect, useState } from 'react'
import Navbar from '../components/Navbar'
import StreakCounter from '../components/StreakCounter'
import AchievementBadge from '../components/AchievementBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import { getStreak, getAchievements } from '../api/gamification'
import { updateInterests } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import type { Streak, Achievement } from '../types'

const ALL_ACHIEVEMENTS = [
  { slug: 'first_steps', name: 'First Steps', description: 'Complete your first module', icon_emoji: '👣' },
  { slug: 'on_a_roll', name: 'On a Roll', description: '3-day streak', icon_emoji: '🎯' },
  { slug: 'week_warrior', name: 'Week Warrior', description: '7-day streak', icon_emoji: '⚔️' },
  { slug: 'perfect_score', name: 'Perfect Score', description: 'Score 100% on a quiz', icon_emoji: '💯' },
  { slug: 'speed_learner', name: 'Speed Learner', description: 'Complete 5 modules', icon_emoji: '⚡' },
  { slug: 'curious_mind', name: 'Curious Mind', description: 'Complete 10 modules', icon_emoji: '🔭' },
  { slug: 'no_hints', name: 'First Try', description: 'Pass without remediation', icon_emoji: '🥇' },
  { slug: 'social_butterfly', name: 'Social Butterfly', description: 'Add your first friend', icon_emoji: '🦋' },
]

export default function Profile() {
  const { user, token, setAuth } = useAuthStore()
  const [streak, setStreak] = useState<Streak | null>(null)
  const [earned, setEarned] = useState<Achievement[]>([])
  const [loading, setLoading] = useState(true)
  const [interests, setInterests] = useState<string[]>(user?.interest_topics ?? [])
  const [newInterest, setNewInterest] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    Promise.all([getStreak(), getAchievements()])
      .then(([s, a]) => {
        setStreak(s.data)
        setEarned(a.data)
      })
      .finally(() => setLoading(false))
  }, [])

  const earnedSlugs = new Set(earned.map((a) => a.slug))

  const addInterest = () => {
    const v = newInterest.trim()
    if (v && !interests.includes(v)) {
      setInterests((prev) => [...prev, v])
    }
    setNewInterest('')
  }

  const removeInterest = (i: string) => {
    setInterests((prev) => prev.filter((x) => x !== i))
  }

  const saveInterests = async () => {
    if (!user || !token) return
    setSaving(true)
    try {
      const { data } = await updateInterests(interests)
      setAuth(token, data)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <LoadingSpinner />
      </>
    )
  }

  const initials = user?.full_name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2) ?? '?'

  return (
    <>
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <div className="w-14 h-14 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold text-xl">
            {initials}
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{user?.full_name}</h1>
            <p className="text-sm text-gray-400">{user?.email}</p>
          </div>
        </div>

        {/* Streak */}
        {streak && (
          <div className="mb-8">
            <StreakCounter current={streak.current_streak} longest={streak.longest_streak} />
          </div>
        )}

        {/* Achievements */}
        <div className="mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Achievements</h2>
          <div className="grid grid-cols-2 gap-3">
            {ALL_ACHIEVEMENTS.map((a) => (
              <AchievementBadge
                key={a.slug}
                emoji={a.icon_emoji}
                name={a.name}
                description={a.description}
                locked={!earnedSlugs.has(a.slug)}
              />
            ))}
          </div>
        </div>

        {/* Interests */}
        <div>
          <h2 className="text-lg font-bold text-gray-900 mb-1">Learning Interests</h2>
          <p className="text-sm text-gray-400 mb-4">Used to personalise your ELI5 explanations.</p>
          <div className="flex flex-wrap gap-2 mb-4">
            {interests.map((i) => (
              <span
                key={i}
                className="flex items-center gap-1 bg-indigo-50 text-indigo-700 text-sm font-medium px-3 py-1 rounded-full border border-indigo-200"
              >
                {i}
                <button
                  onClick={() => removeInterest(i)}
                  className="ml-1 text-indigo-400 hover:text-indigo-700 font-bold"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              value={newInterest}
              onChange={(e) => setNewInterest(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addInterest()}
              placeholder="Add an interest (e.g. Cricket, Cooking)"
              className="flex-1 border border-gray-200 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-indigo-400"
            />
            <button
              onClick={addInterest}
              className="bg-indigo-100 text-indigo-700 font-semibold px-4 py-2 rounded-xl hover:bg-indigo-200 transition-colors text-sm"
            >
              Add
            </button>
          </div>
          <button
            onClick={saveInterests}
            disabled={saving}
            className="mt-4 w-full bg-indigo-600 text-white font-semibold py-3 rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Interests'}
          </button>
        </div>
      </div>
    </>
  )
}
