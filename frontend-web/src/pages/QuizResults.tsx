import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import LoadingSpinner from '../components/LoadingSpinner'
import { remediate } from '../api/learning'
import { useLearningStore } from '../store/learningStore'

export default function QuizResults() {
  const { quizResult, moduleId, quizId, setRemediations } = useLearningStore()
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  if (!quizResult) {
    navigate('/learn/start')
    return null
  }

  const { score, total, passed, failed_concepts } = quizResult
  const pct = Math.round((score / total) * 100)

  const handleRemediate = async () => {
    if (!moduleId || !quizId) return
    setLoading(true)
    try {
      const { data } = await remediate(moduleId, quizId, failed_concepts)
      setRemediations(data.remediations)
      navigate('/remediation')
    } catch {
      setLoading(false)
    }
  }

  return (
    <>
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-12 text-center">
        <div className="text-6xl mb-4">{passed ? '🎉' : '📖'}</div>
        <h1 className="text-3xl font-bold text-forest-900 mb-2">
          {passed ? 'You passed!' : 'Almost there!'}
        </h1>
        <p className="text-gray-400 mb-6">
          You scored <span className="font-bold text-green-600">{score}/{total}</span> ({pct}%)
        </p>

        <div className={`inline-block rounded-2xl px-8 py-4 mb-8 ${passed ? 'bg-green-50 border border-green-200 animate-bounce-success' : 'bg-orange-50 border border-orange-200 animate-shake-error'}`}>
          <p className={`text-lg font-semibold ${passed ? 'text-green-700' : 'text-orange-700'}`}>
            {passed ? 'Module complete — well done!' : `${failed_concepts.length} concept${failed_concepts.length > 1 ? 's' : ''} to review`}
          </p>
        </div>

        {!passed && failed_concepts.length > 0 && (
          <div className="text-left bg-white border-2 border-gray-200 rounded-2xl p-5 mb-8">
            <p className="text-sm font-semibold text-gray-700 mb-3">Concepts to review:</p>
            <ul className="flex flex-col gap-2">
              {failed_concepts.map((c) => (
                <li key={c} className="text-sm text-gray-600 flex items-center gap-2">
                  <span className="text-orange-400">•</span> {c}
                </li>
              ))}
            </ul>
          </div>
        )}

        {loading ? (
          <LoadingSpinner />
        ) : passed ? (
          <button
            onClick={() => navigate('/complete')}
            className="w-full bg-green-600 text-white font-extrabold py-4 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight text-lg"
          >
            Complete Module
          </button>
        ) : (
          <button
            onClick={handleRemediate}
            className="w-full bg-green-600 text-white font-extrabold py-4 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight text-lg"
          >
            Review & Retake
          </button>
        )}
      </div>
    </>
  )
}
