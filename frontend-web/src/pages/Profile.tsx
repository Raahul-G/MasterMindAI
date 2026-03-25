import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Navbar from '../components/Navbar'
import StreakCounter from '../components/StreakCounter'
import AchievementBadge from '../components/AchievementBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import { getStreak, getAchievements } from '../api/gamification'
import { updateInterests, getMe } from '../api/auth'
import { getNotionAuthUrl, disconnectNotion } from '../api/notion'
import { useAuthStore } from '../store/authStore'
import type { Streak, Achievement } from '../types'

const ALL_ACHIEVEMENTS = [
  { slug: 'first_steps', name: 'First Steps', description: 'Complete your first module', icon_emoji: '👣' },
  { slug: 'clean_sweep', name: 'First Try', description: 'Pass without remediation', icon_emoji: '🥇' },
  { slug: 'comeback_kid', name: 'Comeback Kid', description: 'Pass after using remediation', icon_emoji: '💪' },
  { slug: 'knowledge_seeker', name: 'Speed Learner', description: 'Complete 5 modules', icon_emoji: '⚡' },
  { slug: 'scholar', name: 'Curious Mind', description: 'Complete 10 modules', icon_emoji: '🔭' },
  { slug: 'streak_starter', name: 'On a Roll', description: '3-day streak', icon_emoji: '🎯' },
  { slug: 'hot_streak', name: 'Week Warrior', description: '7-day streak', icon_emoji: '⚔️' },
  { slug: 'dedicated', name: 'Dedicated', description: '14-day streak', icon_emoji: '🏆' },
]

export default function Profile() {
  const { user, token, setAuth } = useAuthStore()
  const [searchParams, setSearchParams] = useSearchParams()
  const [streak, setStreak] = useState<Streak | null>(null)
  const [earned, setEarned] = useState<Achievement[]>([])
  const [loading, setLoading] = useState(true)
  const [interests, setInterests] = useState<string[]>(user?.interest_topics ?? [])
  const [newInterest, setNewInterest] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  // Notion state
  const [notionConnected, setNotionConnected] = useState(user?.notion_connected ?? false)
  const [notionWorkspace, setNotionWorkspace] = useState<string | null>(user?.notion_workspace_name ?? null)
  const [notionLoading, setNotionLoading] = useState(false)
  const [notionBanner, setNotionBanner] = useState<'connected' | 'error' | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [s, a] = await Promise.all([getStreak(), getAchievements()])
        setStreak(s.data)
        setEarned(a.data)

        // Refresh user to get latest notion status
        if (token) {
          const { data: me } = await getMe()
          setAuth(token, me)
          setInterests(me.interest_topics ?? [])
          setNotionConnected(me.notion_connected)
          setNotionWorkspace(me.notion_workspace_name)
        }
      } finally {
        setLoading(false)
      }
    }
    load()

    // Handle redirect back from Notion OAuth
    const notionParam = searchParams.get('notion')
    if (notionParam === 'connected') {
      setNotionBanner('connected')
      setSearchParams({}, { replace: true })
    } else if (notionParam === 'error') {
      setNotionBanner('error')
      setSearchParams({}, { replace: true })
    }
  }, [])

  const earnedSlugs = new Set(earned.map((a) => a.slug))

  const addInterest = () => {
    const v = newInterest.trim()
    if (v && !interests.includes(v)) {
      setInterests((prev) => [...prev, v])
      setSaved(false)
    }
    setNewInterest('')
  }

  const removeInterest = (i: string) => {
    setInterests((prev) => prev.filter((x) => x !== i))
    setSaved(false)
  }

  const saveInterests = async () => {
    if (!user || !token) return
    setSaving(true)
    setSaveError(null)
    try {
      const { data } = await updateInterests(interests)
      setAuth(token, data)
      setSaved(true)
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string }
      setSaveError(e?.response?.data?.detail ?? e?.message ?? 'Failed to save interests')
    } finally {
      setSaving(false)
    }
  }

  const handleConnectNotion = async () => {
    setNotionLoading(true)
    try {
      const { data } = await getNotionAuthUrl()
      window.location.href = data.url
    } catch {
      setNotionBanner('error')
      setNotionLoading(false)
    }
  }

  const handleDisconnectNotion = async () => {
    setNotionLoading(true)
    try {
      await disconnectNotion()
      setNotionConnected(false)
      setNotionWorkspace(null)
      if (user && token) {
        setAuth(token, { ...user, notion_connected: false, notion_workspace_name: null })
      }
    } finally {
      setNotionLoading(false)
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
          <div className="w-14 h-14 rounded-full bg-green-600 flex items-center justify-center text-white font-bold text-xl">
            {initials}
          </div>
          <div>
            <h1 className="text-xl font-bold text-forest-900">{user?.full_name}</h1>
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
          <h2 className="text-lg font-bold text-forest-900 mb-4">Achievements</h2>
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
        <div className="mb-8">
          <h2 className="text-lg font-bold text-forest-900 mb-1">Learning Interests</h2>
          <p className="text-sm text-gray-400 mb-4">Used to personalise your ELI5 explanations.</p>
          <div className="flex flex-wrap gap-2 mb-4">
            {interests.map((i) => (
              <span
                key={i}
                className={`flex items-center gap-1 text-sm font-medium px-3 py-1 rounded-full border transition-colors ${
                  saved
                    ? 'bg-green-50 text-green-700 border-green-300'
                    : 'bg-green-50 text-green-700 border-green-200'
                }`}
              >
                {i}
                <button
                  onClick={() => removeInterest(i)}
                  className={`ml-1 font-bold ${saved ? 'text-green-400 hover:text-green-700' : 'text-green-500 hover:text-green-700'}`}
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
              className="flex-1 border border-gray-200 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-green-500"
            />
            <button
              onClick={addInterest}
              className="bg-green-100 text-green-700 font-semibold px-4 py-2 rounded-xl hover:bg-green-200 transition-colors text-sm"
            >
              Add
            </button>
          </div>
          <button
            onClick={saveInterests}
            disabled={saving}
            className={`mt-4 w-full font-extrabold py-3 rounded-2xl border-b-4 border-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight disabled:opacity-50 bg-green-600 text-white hover:bg-green-700`}
          >
            {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Interests'}
          </button>
          {saveError && (
            <p className="mt-2 text-sm text-red-500 text-center">{saveError}</p>
          )}
        </div>

        {/* Notion Integration */}
        <div>
          <h2 className="text-lg font-bold text-forest-900 mb-1">Notion</h2>
          <p className="text-sm text-gray-400 mb-4">
            Connect your Notion workspace. Every completed module will automatically appear as a sub-page.
          </p>

          {notionBanner === 'connected' && (
            <div className="mb-4 px-4 py-3 bg-green-50 border border-green-200 rounded-xl text-sm text-green-700 font-medium">
              Notion connected! Your MasterMind page has been created.
            </div>
          )}
          {notionBanner === 'error' && (
            <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">
              Something went wrong connecting Notion. Please try again.
            </div>
          )}

          {notionConnected ? (
            <div className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3">
              <div className="flex items-center gap-3">
                <span className="text-xl">N</span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">
                    {notionWorkspace ?? 'Notion'}
                  </p>
                  <p className="text-xs text-green-600">Connected</p>
                </div>
              </div>
              <button
                onClick={handleDisconnectNotion}
                disabled={notionLoading}
                className="text-sm text-red-400 hover:text-red-600 font-medium disabled:opacity-50"
              >
                {notionLoading ? 'Disconnecting...' : 'Disconnect'}
              </button>
            </div>
          ) : (
            <button
              onClick={handleConnectNotion}
              disabled={notionLoading}
              className="w-full flex items-center justify-center gap-2 bg-gray-900 text-white font-extrabold py-3 rounded-2xl border-b-4 border-gray-700 hover:bg-gray-800 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight disabled:opacity-50"
            >
              <span className="text-lg font-bold">N</span>
              {notionLoading ? 'Redirecting...' : 'Connect Notion'}
            </button>
          )}
        </div>
      </div>
    </>
  )
}
