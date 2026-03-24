import { useEffect, useState, useRef } from 'react'
import Navbar from '../components/Navbar'
import LoadingSpinner from '../components/LoadingSpinner'
import {
  getFriends, getFriendRequests, sendFriendRequest,
  acceptFriendRequest, getFeed, searchUsers,
} from '../api/social'
import type { FriendResponse, FriendRequestResponse, ActivityFeedItem, UserSearchResult } from '../types'

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function feedDescription(item: ActivityFeedItem): string {
  const m = item.metadata
  if (item.activity_type === 'module_completed') {
    return `finished learning "${m.topic}" — ${m.score}/${m.total}`
  }
  if (item.activity_type === 'achievement_earned') {
    return `earned the "${m.name}" badge`
  }
  return item.activity_type
}

export default function Friends() {
  const [friends, setFriends] = useState<FriendResponse[]>([])
  const [requests, setRequests] = useState<FriendRequestResponse[]>([])
  const [feed, setFeed] = useState<ActivityFeedItem[]>([])
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [searchLoading, setSearchLoading] = useState(false)
  const [sentIds, setSentIds] = useState<Set<string>>(new Set())
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    Promise.all([getFriends(), getFriendRequests(), getFeed()])
      .then(([f, r, fd]) => {
        setFriends(f.data)
        setRequests(r.data)
        setFeed(fd.data)
      })
      .finally(() => setLoading(false))
  }, [])

  const handleSearch = (value: string) => {
    setQuery(value)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (value.trim().length < 2) {
      setSearchResults([])
      return
    }
    debounceRef.current = setTimeout(async () => {
      setSearchLoading(true)
      try {
        const { data } = await searchUsers(value.trim())
        setSearchResults(data)
      } finally {
        setSearchLoading(false)
      }
    }, 300)
  }

  const handleSendRequest = async (id: string) => {
    await sendFriendRequest(id)
    setSentIds((prev) => new Set(prev).add(id))
  }

  const handleAccept = async (id: string) => {
    await acceptFriendRequest(id)
    setRequests((prev) => prev.filter((r) => r.id !== id))
    const updated = await getFriends()
    setFriends(updated.data)
  }

  const initials = (name: string) =>
    name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)

  if (loading) {
    return (
      <>
        <Navbar />
        <LoadingSpinner />
      </>
    )
  }

  return (
    <>
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-forest-900 mb-6">Friends</h1>

        {/* Search */}
        <div className="mb-8">
          <label className="text-sm font-medium text-gray-700 block mb-2">Find people</label>
          <input
            value={query}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search by name..."
            className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-green-500"
          />
          {searchLoading && <p className="text-xs text-gray-400 mt-2">Searching...</p>}
          {searchResults.length > 0 && (
            <div className="mt-2 border-2 border-gray-200 rounded-xl overflow-hidden">
              {searchResults.map((u) => (
                <div key={u.id} className="flex items-center justify-between px-4 py-3 bg-white hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-700 text-xs font-bold">
                      {initials(u.full_name)}
                    </div>
                    <span className="text-sm font-medium text-gray-800">{u.full_name}</span>
                  </div>
                  <button
                    onClick={() => handleSendRequest(u.id)}
                    disabled={sentIds.has(u.id)}
                    className="text-xs font-semibold text-green-600 hover:underline disabled:text-gray-400"
                  >
                    {sentIds.has(u.id) ? 'Sent' : 'Add Friend'}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Incoming requests */}
        {requests.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-bold text-forest-900 mb-3">Friend Requests</h2>
            <div className="flex flex-col gap-2">
              {requests.map((r) => (
                <div key={r.id} className="flex items-center justify-between bg-white border-2 border-gray-200 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-700 text-xs font-bold">
                      {initials(r.requester.full_name)}
                    </div>
                    <span className="text-sm font-medium text-gray-800">{r.requester.full_name}</span>
                  </div>
                  <button
                    onClick={() => handleAccept(r.id)}
                    className="text-xs font-extrabold bg-green-600 text-white px-3 py-1.5 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight"
                  >
                    Accept
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Friends list */}
        <div className="mb-8">
          <h2 className="text-lg font-bold text-forest-900 mb-3">Your Friends ({friends.length})</h2>
          {friends.length === 0 ? (
            <p className="text-sm text-gray-400">No friends yet — search above to add some.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {friends.map((f) => (
                <div key={f.id} className="flex items-center justify-between bg-white border-2 border-gray-200 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-700 text-xs font-bold">
                      {initials(f.full_name)}
                    </div>
                    <span className="text-sm font-medium text-gray-800">{f.full_name}</span>
                  </div>
                  <span className="flex items-center gap-1 text-xs text-orange-600 font-medium">
                    🔥 {f.current_streak}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Activity feed */}
        <div>
          <h2 className="text-lg font-bold text-forest-900 mb-3">Activity Feed</h2>
          {feed.length === 0 ? (
            <p className="text-sm text-gray-400">No recent activity. Add friends to see what they're learning.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {feed.map((item) => (
                <div key={item.id} className="flex items-start gap-3 bg-white border-2 border-gray-200 rounded-xl px-4 py-3">
                  <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-700 text-xs font-bold flex-shrink-0">
                    {initials(item.user.full_name)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-semibold text-gray-800">{item.user.full_name} </span>
                    <span className="text-sm text-gray-500">{feedDescription(item)}</span>
                  </div>
                  <span className="text-xs text-gray-300 flex-shrink-0">{timeAgo(item.created_at)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
