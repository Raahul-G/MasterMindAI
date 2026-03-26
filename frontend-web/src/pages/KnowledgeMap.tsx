import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import LoadingSpinner from '../components/LoadingSpinner'
import { getKnowledgeMap, backfillRecommendations } from '../api/learning'
import type { KnowledgeMapTopic, ConceptNode } from '../types'

export default function KnowledgeMap() {
  const [topics, setTopics] = useState<KnowledgeMapTopic[]>([])
  const [loading, setLoading] = useState(true)
  const [backfilling, setBackfilling] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await getKnowledgeMap()
        setTopics(data.topics)
        setLoading(false)

        const hasLearned = data.topics.some((t) => t.nodes.some((n) => n.status === 'learned'))
        const hasRecommended = data.topics.some((t) => t.nodes.some((n) => n.status === 'recommended'))

        if (hasLearned && !hasRecommended) {
          setBackfilling(true)
          try {
            await backfillRecommendations()
            const { data: refreshed } = await getKnowledgeMap()
            setTopics(refreshed.topics)
          } catch {
            // backfill failed silently — map still shows with learned concepts
          } finally {
            setBackfilling(false)
          }
        }
      } catch {
        setError('Failed to load knowledge map.')
        setLoading(false)
      }
    }
    load()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleStartRecommended = (node: ConceptNode) => {
    navigate('/learn/start', {
      state: {
        topic: node.concept,
        prerequisite_concepts: node.prerequisite_concepts ?? [],
      },
    })
  }

  return (
    <>
      <Navbar />
      <div className="max-w-3xl mx-auto px-6 py-10">
        <h1 className="text-3xl font-extrabold text-gray-900 mb-1">Knowledge Map</h1>
        <p className="text-gray-400 mb-8 text-sm">Your learning history and what to unlock next.</p>

        {loading && <LoadingSpinner />}
        {error && <p className="text-red-500 text-sm">{error}</p>}

        {backfilling && (
          <div className="flex items-center gap-3 text-sm text-purple-600 bg-purple-50 border border-purple-200 rounded-xl px-4 py-3 mb-6">
            <svg className="animate-spin h-4 w-4 text-purple-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            Generating your recommendations...
          </div>
        )}

        {!loading && !error && topics.length === 0 && (
          <div className="text-center py-20 text-gray-400">
            <p className="text-5xl mb-4">🗺️</p>
            <p className="text-lg font-semibold text-gray-600 mb-2">Your map is empty</p>
            <p className="text-sm mb-6">Complete a module to unlock your knowledge graph.</p>
            <Link
              to="/learn/start"
              className="inline-block bg-green-600 text-white font-bold px-6 py-3 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75"
            >
              Start Learning
            </Link>
          </div>
        )}

        {topics.map((t) => {
          const learned = t.nodes.filter((n) => n.status === 'learned')
          const recommended = t.nodes.filter((n) => n.status === 'recommended')
          return (
            <div key={t.topic} className="mb-10">
              <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <span className="text-purple-500">📚</span> {t.topic}
              </h2>

              {learned.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Learned</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {learned.map((node) => (
                      <div
                        key={node.concept}
                        className="flex items-start gap-3 bg-green-50 border border-green-200 rounded-xl px-4 py-3"
                      >
                        <span className="text-green-500 text-lg mt-0.5">✓</span>
                        <div>
                          <p className="font-semibold text-green-800 text-sm">{node.concept}</p>
                          {node.module_id && (
                            <Link
                              to={`/modules/${node.module_id}/review`}
                              className="text-xs text-green-600 hover:underline"
                            >
                              Review module
                            </Link>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {recommended.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Unlock Next</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {recommended.map((node) => (
                      <div
                        key={node.concept}
                        className="flex items-start gap-3 bg-purple-50 border border-purple-200 rounded-xl px-4 py-3"
                      >
                        <span className="text-purple-400 text-lg mt-0.5">→</span>
                        <div className="flex-1">
                          <p className="font-semibold text-purple-800 text-sm">{node.concept}</p>
                          {node.reason && (
                            <p className="text-xs text-purple-600 mt-0.5">{node.reason}</p>
                          )}
                          <button
                            onClick={() => handleStartRecommended(node)}
                            className="mt-2 text-xs font-bold bg-purple-600 text-white px-3 py-1.5 rounded-lg border-b-2 border-purple-700 hover:bg-purple-700 active:translate-y-[1px] active:border-b-[1px] transition-[transform,border-bottom-width] duration-75"
                          >
                            Start Learning
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </>
  )
}
