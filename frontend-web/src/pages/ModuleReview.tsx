import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import PassageCard from '../components/PassageCard'
import LoadingSpinner from '../components/LoadingSpinner'
import { getModuleReview } from '../api/modules'
import type { ModuleReview } from '../types'

const LEVEL_LABELS: Record<string, string> = { kid: 'Kid', intermediate: 'Intermediate', expert: 'Expert' }

export default function ModuleReview() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [review, setReview] = useState<ModuleReview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    getModuleReview(id)
      .then((res) => setReview(res.data))
      .catch((err) => setError(err?.response?.data?.detail ?? err?.message ?? 'Failed to load review'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <><Navbar /><LoadingSpinner /></>

  if (error) return (
    <>
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-12 text-center">
        <p className="text-red-500 font-medium mb-2">Could not load review</p>
        <p className="text-sm text-gray-400 mb-6">{error}</p>
        <button onClick={() => navigate('/dashboard')} className="text-indigo-600 font-medium hover:underline">
          Back to Dashboard
        </button>
      </div>
    </>
  )
  if (!review) return null

  return (
    <>
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-2">
          <span className="text-xs font-bold text-indigo-500 uppercase tracking-wide">
            {LEVEL_LABELS[review.level] ?? review.level}
          </span>
          <h1 className="text-2xl font-bold text-gray-900 mt-0.5">{review.topic}</h1>
          {review.quiz_score !== null && (
            <p className="text-sm text-gray-400 mt-1">
              Final score: <span className="font-semibold text-indigo-600">{review.quiz_score}/{review.quiz_total}</span>
              {review.quiz_attempts && review.quiz_attempts > 1 && (
                <span className="ml-2 text-gray-400">({review.quiz_attempts} attempts)</span>
              )}
            </p>
          )}
          {review.completed_at && (
            <p className="text-xs text-gray-400 mt-0.5">
              Completed {new Date(review.completed_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}
            </p>
          )}
        </div>

        {/* ELI5 */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-5 mb-6 flex gap-3 mt-4">
          <span className="text-2xl">💡</span>
          <div>
            <p className="text-xs font-bold text-yellow-700 mb-1 uppercase tracking-wide">Simple Explanation</p>
            <p className="text-gray-700 leading-relaxed">{review.eli5_text}</p>
          </div>
        </div>

        {/* Passages */}
        <h2 className="text-lg font-bold text-gray-900 mb-3">Core Concepts</h2>
        {review.passages.map((p, i) => (
          <PassageCard key={p.id} title={p.concept_title} content={p.content} index={i} />
        ))}

        {/* Quiz Q&A */}
        {review.questions.length > 0 && (
          <div className="mt-8">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Quiz Review</h2>
            <div className="flex flex-col gap-4">
              {review.questions.map((q, i) => (
                <div key={i} className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
                  <p className="font-semibold text-gray-800 mb-1 text-sm">{q.concept_title}</p>
                  <p className="text-gray-900 mb-3">{q.question_text}</p>
                  <div className="flex flex-col gap-2">
                    {q.options.map((opt) => {
                      const isCorrect = opt === q.correct_answer
                      const cls = isCorrect
                        ? 'px-4 py-2.5 rounded-xl border-2 text-sm flex items-center justify-between border-green-400 bg-green-50 text-green-800'
                        : 'px-4 py-2.5 rounded-xl border-2 text-sm flex items-center justify-between border-gray-100 bg-gray-50 text-gray-500'
                      return (
                        <div key={opt} className={cls}>
                          <span>{opt}</span>
                          {isCorrect && <span>✓</span>}
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <button
          onClick={() => navigate('/dashboard')}
          className="mt-8 w-full bg-indigo-600 text-white font-semibold py-3 rounded-xl hover:bg-indigo-700 transition-colors"
        >
          Back to Dashboard
        </button>
      </div>
    </>
  )
}
