import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar'
import ThinkingCard from '../components/ThinkingCard'
import { startModule } from '../api/learning'
import { useLearningStore } from '../store/learningStore'

const LEVELS = [
  { id: 'kid', label: 'Kid', desc: 'Simple analogies, no jargon', emoji: '🧒' },
  { id: 'intermediate', label: 'Intermediate', desc: 'University or curious adult', emoji: '🎓' },
  { id: 'expert', label: 'Expert', desc: 'Graduate level', emoji: '🔬' },
] as const

const CONCEPT_THOUGHTS = [
  { icon: '🧐', text: "Reading the 'grown-up' version..." },
  { icon: '🔍', text: 'Identifying the tricky concepts...' },
  { icon: '💡', text: 'Searching for a perfect analogy...' },
  { icon: '✂️', text: 'Replacing big words with small ones...' },
  { icon: '✨', text: 'Making it easy to understand...' },
]

export default function TopicSelection() {
  const location = useLocation()
  const locationState = location.state as { topic?: string; prerequisite_concepts?: string[] } | null

  const [topic, setTopic] = useState(locationState?.topic ?? '')
  const [level, setLevel] = useState<'kid' | 'intermediate' | 'expert'>('intermediate')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const setStart = useLearningStore((s) => s.setStart)
  const navigate = useNavigate()

  const prerequisiteConcepts = locationState?.prerequisite_concepts ?? []

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!topic.trim()) return
    setError('')
    setLoading(true)
    try {
      const { data } = await startModule(topic.trim(), level, prerequisiteConcepts.length > 0 ? prerequisiteConcepts : undefined)
      setStart(data)
      navigate('/learn')
    } catch {
      setError('Failed to start module. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-forest-900 mb-2">What do you want to learn?</h1>
        <p className="text-gray-400 mb-8">Pick any topic — AI will teach it to you step by step.</p>

        {prerequisiteConcepts.length > 0 && (
          <div className="mb-6 bg-purple-50 border border-purple-200 rounded-xl px-4 py-3 text-sm text-purple-700">
            Builds on: <span className="font-semibold">{prerequisiteConcepts.join(', ')}</span>
          </div>
        )}

        <form onSubmit={handleStart} className="flex flex-col gap-6">
          <div>
            <label htmlFor="topic" className="text-sm font-medium text-gray-700 block mb-2">Topic</label>
            <input
              id="topic"
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              required
              placeholder='e.g. "Quantum entanglement" or "How the internet works"'
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-base focus:outline-none focus:border-green-500"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 block mb-2">Level</label>
            <div className="grid grid-cols-3 gap-3">
              {LEVELS.map((l) => (
                <button
                  key={l.id}
                  type="button"
                  onClick={() => setLevel(l.id)}
                  className={`flex flex-col items-center p-4 rounded-xl border-2 transition-all ${
                    level === l.id
                      ? 'border-green-500 bg-green-50'
                      : 'border-gray-200 hover:border-green-400 bg-white'
                  }`}
                >
                  <span className="text-2xl mb-1">{l.emoji}</span>
                  <span className={`font-semibold text-sm ${level === l.id ? 'text-green-700' : 'text-gray-700'}`}>
                    {l.label}
                  </span>
                  <span className="text-xs text-gray-400 mt-0.5 text-center">{l.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          {loading ? (
            <ThinkingCard thoughts={CONCEPT_THOUGHTS} />
          ) : (
            <button
              type="submit"
              className="bg-green-600 text-white font-extrabold py-4 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight text-lg"
            >
              Start Learning
            </button>
          )}
        </form>
      </div>
    </>
  )
}
