import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import LoadingSpinner from '../components/LoadingSpinner'
import { startModule } from '../api/learning'
import { useLearningStore } from '../store/learningStore'

const LEVELS = [
  { id: 'kid', label: 'Kid', desc: 'Simple analogies, no jargon', emoji: '🧒' },
  { id: 'intermediate', label: 'Intermediate', desc: 'University or curious adult', emoji: '🎓' },
  { id: 'expert', label: 'Expert', desc: 'Graduate level', emoji: '🔬' },
] as const

export default function TopicSelection() {
  const [topic, setTopic] = useState('')
  const [level, setLevel] = useState<'kid' | 'intermediate' | 'expert'>('intermediate')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const setModule = useLearningStore((s) => s.setModule)
  const navigate = useNavigate()

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!topic.trim()) return
    setError('')
    setLoading(true)
    try {
      const { data } = await startModule(topic.trim(), level)
      setModule(data.module_id, topic.trim(), level, data.eli5_text, data.passages)
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">What do you want to learn?</h1>
        <p className="text-gray-400 mb-8">Pick any topic — AI will teach it to you step by step.</p>

        <form onSubmit={handleStart} className="flex flex-col gap-6">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-2">Topic</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              required
              placeholder='e.g. "Quantum entanglement" or "How the internet works"'
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-base focus:outline-none focus:border-indigo-400"
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
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-indigo-300 bg-white'
                  }`}
                >
                  <span className="text-2xl mb-1">{l.emoji}</span>
                  <span className={`font-semibold text-sm ${level === l.id ? 'text-indigo-700' : 'text-gray-700'}`}>
                    {l.label}
                  </span>
                  <span className="text-xs text-gray-400 mt-0.5 text-center">{l.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          {loading ? (
            <LoadingSpinner />
          ) : (
            <button
              type="submit"
              className="bg-indigo-600 text-white font-semibold py-4 rounded-xl hover:bg-indigo-700 transition-colors text-lg"
            >
              Start Learning
            </button>
          )}
        </form>
      </div>
    </>
  )
}
