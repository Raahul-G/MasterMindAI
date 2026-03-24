import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import PassageCard from '../components/PassageCard'
import LoadingSpinner from '../components/LoadingSpinner'
import { generateQuiz } from '../api/learning'
import { useLearningStore } from '../store/learningStore'

export default function Remediation() {
  const { remediations, moduleId, setQuiz } = useLearningStore()
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  if (remediations.length === 0 || !moduleId) {
    navigate('/learn/start')
    return null
  }

  const handleRetake = async () => {
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
        <div className="mb-6">
          <span className="text-xs font-bold text-orange-500 uppercase tracking-wide">Let's try again</span>
          <h1 className="text-2xl font-bold text-forest-900 mt-0.5">Revised Explanations</h1>
          <p className="text-gray-400 text-sm mt-1">Different analogies for the concepts you missed.</p>
        </div>

        {remediations.map((r, i) => (
          <PassageCard key={i} title={r.concept_title} content={r.content} index={i} revised />
        ))}

        <div className="mt-8">
          {loading ? (
            <LoadingSpinner />
          ) : (
            <button
              onClick={handleRetake}
              className="w-full bg-green-600 text-white font-extrabold py-4 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight text-lg"
            >
              Retake Quiz
            </button>
          )}
        </div>
      </div>
    </>
  )
}
