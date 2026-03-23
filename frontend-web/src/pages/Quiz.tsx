import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import QuizCard from '../components/QuizCard'
import ProgressBar from '../components/ProgressBar'
import LoadingSpinner from '../components/LoadingSpinner'
import { submitQuiz } from '../api/learning'
import { useLearningStore } from '../store/learningStore'
import type { AnswerSubmission } from '../types'

export default function Quiz() {
  const { quizId, questions, setQuizResult, moduleId } = useLearningStore()
  const [current, setCurrent] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  if (!quizId || questions.length === 0) {
    navigate(moduleId ? '/learn' : '/learn/start')
    return null
  }

  const q = questions[current]
  const isLast = current === questions.length - 1
  const selected = answers[q.id] ?? null

  const handleNext = async () => {
    if (!selected) return
    if (!isLast) {
      setCurrent((c) => c + 1)
      return
    }
    setSubmitting(true)
    const submissions: AnswerSubmission[] = questions.map((question) => ({
      question_id: question.id,
      user_answer: answers[question.id] ?? '',
    }))
    try {
      const { data } = await submitQuiz(quizId, submissions)
      setQuizResult(data)
      navigate('/quiz/results')
    } catch {
      setSubmitting(false)
    }
  }

  return (
    <>
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-8">
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-400 mb-2">
            <span>Question {current + 1} of {questions.length}</span>
            <span>{q.concept_title}</span>
          </div>
          <ProgressBar current={current + 1} total={questions.length} />
        </div>

        <div className="mt-6">
          <QuizCard
            question={q.question_text}
            options={q.options}
            selected={selected}
            onSelect={(opt) => setAnswers((prev) => ({ ...prev, [q.id]: opt }))}
          />
        </div>

        {submitting ? (
          <LoadingSpinner />
        ) : (
          <button
            onClick={handleNext}
            disabled={!selected}
            className="mt-6 w-full bg-indigo-600 text-white font-semibold py-4 rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-40 text-lg"
          >
            {isLast ? 'Submit Quiz' : 'Next'}
          </button>
        )}
      </div>
    </>
  )
}
