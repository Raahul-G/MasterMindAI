import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import PassageCard from '../components/PassageCard'
import LoadingSpinner from '../components/LoadingSpinner'
import { generateQuiz } from '../api/learning'
import { useLearningStore } from '../store/learningStore'

export default function Learning() {
  const { moduleId, topic, level, eli5Text, passages, setQuiz } = useLearningStore()
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  if (!moduleId) {
    navigate('/learn/start')
    return null
  }

  const handleTakeQuiz = async () => {
    setLoading(true)
    try {
      const { data } = await generateQuiz(moduleId)
      setQuiz(data.quiz_id, data.questions)
      navigate('/quiz')
    } catch {
      setLoading(false)
    }
  }

  return (
    <>
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-8">
        <div className="mb-2">
          <span className="text-xs font-bold text-green-600 uppercase tracking-wide">{level}</span>
          <h1 className="text-2xl font-bold text-forest-900 mt-0.5">{topic}</h1>
        </div>

        {eli5Text && (
          <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5 mb-6 flex gap-3">
            <span className="text-2xl">💡</span>
            <div>
              <p className="text-xs font-bold text-blue-700 mb-1 uppercase tracking-wide">Simple Explanation</p>
              <p className="text-gray-700 leading-relaxed">{eli5Text}</p>
            </div>
          </div>
        )}

        <div className="mb-8">
          {passages.map((p, i) => (
            <PassageCard key={p.id} title={p.concept_title} content={p.content} index={i} />
          ))}
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : (
          <button
            onClick={handleTakeQuiz}
            className="w-full bg-green-600 text-white font-extrabold py-4 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight text-lg"
          >
            Take the Quiz
          </button>
        )}
      </div>
    </>
  )
}
