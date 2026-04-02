import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import PassageCard from '../components/PassageCard'
import QuizCard from '../components/QuizCard'
import ThinkingCard from '../components/ThinkingCard'
import { submitQuiz, remediate, generateQuiz, nextPair } from '../api/learning'
import { useLearningStore } from '../store/learningStore'
import type { AnswerSubmission, Remediation, Question } from '../types'

type Phase =
  | 'reading'
  | 'quizzing'
  | 'submitting'
  | 'failed'
  | 'remediating_loading'
  | 'remediating'
  | 'retry_loading'
  | 'passed'
  | 'pair_loading'
  | 'needs_pair'

const CONCEPT_THOUGHTS = [
  { icon: '🧐', text: "Reading the 'grown-up' version..." },
  { icon: '🔍', text: 'Identifying the tricky concepts...' },
  { icon: '💡', text: 'Searching for a perfect analogy...' },
  { icon: '✂️', text: 'Replacing big words with small ones...' },
  { icon: '✨', text: 'Making it easy to understand...' },
]

const QUIZ_THOUGHTS = [
  { icon: '📝', text: 'Reading your explanation carefully...' },
  { icon: '🎯', text: 'Finding what matters most...' },
  { icon: '🤔', text: 'Crafting tricky questions...' },
  { icon: '✅', text: 'Double-checking the answers...' },
]

const SUBMIT_THOUGHTS = [
  { icon: '📊', text: 'Checking your answers...' },
  { icon: '🧮', text: 'Calculating your score...' },
]

const REMEDIATION_THOUGHTS = [
  { icon: '🔄', text: 'Finding a different angle...' },
  { icon: '🎨', text: 'Crafting a new analogy...' },
  { icon: '📖', text: 'Rewriting with fresh examples...' },
  { icon: '✨', text: 'Making it clearer this time...' },
]

export default function Learning() {
  const {
    moduleId,
    eli5Text,
    currentPassage,
    quizId,
    questions,
    conceptsLearned,
    setPassage,
    setConceptsLearned,
  } = useLearningStore()

  const [phase, setPhase] = useState<Phase>('reading')
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [score, setScore] = useState<{ correct: number; total: number } | null>(null)
  const [failedConcepts, setFailedConcepts] = useState<string[]>([])
  const [remediations, setRemediations] = useState<Remediation[]>([])
  const [activeQuizId, setActiveQuizId] = useState<string>(quizId ?? '')
  const [activeQuestions, setActiveQuestions] = useState<Question[]>(questions)

  const navigate = useNavigate()

  if (!moduleId || !currentPassage) {
    navigate('/learn/start')
    return null
  }

  const allAnswered = activeQuestions.every((q) => answers[q.id])

  const handleSubmitQuiz = async () => {
    setPhase('submitting')
    const submissions: AnswerSubmission[] = activeQuestions.map((q) => ({
      question_id: q.id,
      user_answer: answers[q.id] ?? '',
    }))
    try {
      const { data } = await submitQuiz(activeQuizId, submissions)
      setScore({ correct: data.score, total: data.total })
      setConceptsLearned(data.concepts_learned)

      if (!data.passed) {
        setFailedConcepts(data.failed_concepts)
        setPhase('failed')
        return
      }

      if (data.next_passage && data.next_quiz_id && data.next_questions.length > 0) {
        // Auto-advance to next passage in same pair
        setPassage(data.next_passage, data.next_quiz_id, data.next_questions, data.concepts_learned)
        setAnswers({})
        setActiveQuizId(data.next_quiz_id)
        setActiveQuestions(data.next_questions)
        setScore(null)
        setPhase('reading')
        return
      }

      if (data.needs_new_pair) {
        setPhase('needs_pair')
        return
      }

      setPhase('passed')
    } catch {
      setPhase('quizzing')
    }
  }

  const handleRemediate = async () => {
    setPhase('remediating_loading')
    try {
      const { data } = await remediate(moduleId, activeQuizId, failedConcepts)
      setRemediations(data.remediations)
      setPhase('remediating')
    } catch {
      setPhase('failed')
    }
  }

  const handleRetry = async () => {
    setPhase('retry_loading')
    try {
      const { data } = await generateQuiz(currentPassage.id)
      setActiveQuizId(data.quiz_id)
      setActiveQuestions(data.questions)
      setAnswers({})
      setScore(null)
      setPhase('quizzing')
    } catch {
      setPhase('remediating')
    }
  }

  const handleNextPair = async () => {
    setPhase('pair_loading')
    const coveredConcepts = useLearningStore.getState().currentPassage
      ? [useLearningStore.getState().currentPassage!.concept_title]
      : []
    try {
      const { data } = await nextPair(moduleId, coveredConcepts)
      setPassage(data.current_passage, data.quiz_id, data.questions, data.concepts_learned)
      setAnswers({})
      setActiveQuizId(data.quiz_id)
      setActiveQuestions(data.questions)
      setScore(null)
      setRemediations([])
      setPhase('reading')
    } catch {
      setPhase('needs_pair')
    }
  }

  return (
    <>
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-forest-900">{currentPassage.concept_title}</h1>
            <p className="text-xs text-gray-400 mt-0.5">Concept {currentPassage.order_index}</p>
          </div>
          <span className="text-sm font-semibold text-green-600">
            {conceptsLearned} learned
          </span>
        </div>

        {/* Big Idea */}
        {eli5Text && phase === 'reading' && currentPassage.order_index === 1 && (
          <div className="bg-purple-50 border border-purple-200 rounded-2xl p-5 mb-6 flex gap-3">
            <span className="text-2xl">💡</span>
            <div>
              <p className="text-xs font-bold text-purple-700 mb-1 uppercase tracking-wide">Big Idea</p>
              <p className="text-gray-700 leading-relaxed text-sm">{eli5Text}</p>
            </div>
          </div>
        )}

        {/* READING PHASE */}
        {phase === 'reading' && (
          <>
            <PassageCard
              title={currentPassage.concept_title}
              summary={currentPassage.summary}
              content={currentPassage.content}
              use_cases={currentPassage.use_cases}
              index={currentPassage.order_index - 1}
            />
            <button
              onClick={() => setPhase('quizzing')}
              className="w-full mt-4 bg-green-600 text-white font-extrabold py-4 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight text-lg"
            >
              Test my understanding
            </button>
          </>
        )}

        {/* QUIZZING PHASE */}
        {phase === 'quizzing' && (
          <>
            <div className="flex flex-col gap-4 mb-6">
              {activeQuestions.map((q, i) => (
                <div key={q.id}>
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-wide mb-2">
                    Question {i + 1} of {activeQuestions.length}
                  </p>
                  <QuizCard
                    question={q.question_text}
                    options={q.options}
                    selected={answers[q.id] ?? null}
                    onSelect={(opt) => setAnswers((prev) => ({ ...prev, [q.id]: opt }))}
                  />
                </div>
              ))}
            </div>
            <button
              onClick={handleSubmitQuiz}
              disabled={!allAnswered}
              className="w-full bg-green-600 text-white font-extrabold py-4 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight disabled:opacity-40 text-lg"
            >
              Submit
            </button>
          </>
        )}

        {/* THINKING STATES */}
        {phase === 'submitting' && <ThinkingCard thoughts={SUBMIT_THOUGHTS} intervalMs={1500} />}
        {phase === 'pair_loading' && <ThinkingCard thoughts={CONCEPT_THOUGHTS} />}
        {phase === 'retry_loading' && <ThinkingCard thoughts={QUIZ_THOUGHTS} />}
        {phase === 'remediating_loading' && <ThinkingCard thoughts={REMEDIATION_THOUGHTS} />}

        {/* FAILED PHASE */}
        {phase === 'failed' && score && (
          <div className="flex flex-col gap-4">
            <div className="bg-red-50 border border-red-200 rounded-2xl p-5 text-center">
              <p className="text-3xl font-extrabold text-red-600 mb-1">{score.correct}/{score.total}</p>
              <p className="text-sm text-red-500 font-medium">Not quite — let's review</p>
            </div>
            <div className="bg-white border border-gray-100 rounded-2xl p-4">
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wide mb-2">Missed concept</p>
              {failedConcepts.map((c) => (
                <p key={c} className="text-sm font-semibold text-forest-900">{c}</p>
              ))}
            </div>
            <button
              onClick={handleRemediate}
              className="w-full bg-orange-500 text-white font-extrabold py-4 rounded-2xl border-b-4 border-orange-600 hover:bg-orange-600 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight text-lg"
            >
              See new explanation
            </button>
          </div>
        )}

        {/* REMEDIATING PHASE */}
        {phase === 'remediating' && (
          <>
            <div className="mb-4">
              <span className="text-xs font-bold text-orange-500 uppercase tracking-wide">Let's try again</span>
              <h2 className="text-lg font-bold text-forest-900 mt-0.5">Different explanation</h2>
            </div>
            {remediations.map((r, i) => (
              <PassageCard key={i} title={r.concept_title} content={r.content} index={i} revised />
            ))}
            <button
              onClick={handleRetry}
              className="w-full mt-4 bg-green-600 text-white font-extrabold py-4 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight text-lg"
            >
              Try again
            </button>
          </>
        )}

        {/* PASSED PHASE (end of module, no next pair) */}
        {phase === 'passed' && score && (
          <div className="flex flex-col gap-4 text-center">
            <div className="bg-green-50 border border-green-200 rounded-2xl p-6">
              <p className="text-3xl font-extrabold text-green-600 mb-1">{score.correct}/{score.total}</p>
              <p className="text-sm text-green-600 font-bold uppercase tracking-wide">Concept mastered!</p>
              <p className="text-gray-400 text-sm mt-1">{conceptsLearned} concepts learned in this module</p>
            </div>
            <button
              onClick={() => navigate('/dashboard')}
              className="w-full bg-green-600 text-white font-extrabold py-4 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight text-lg"
            >
              Back to Dashboard
            </button>
          </div>
        )}

        {/* NEEDS PAIR PHASE */}
        {phase === 'needs_pair' && score && (
          <div className="flex flex-col gap-4">
            <div className="bg-green-50 border border-green-200 rounded-2xl p-5 text-center">
              <p className="text-3xl font-extrabold text-green-600 mb-1">{score.correct}/{score.total}</p>
              <p className="text-sm text-green-600 font-bold uppercase tracking-wide">Concept mastered!</p>
              <p className="text-gray-400 text-sm mt-1">{conceptsLearned} concepts learned so far</p>
            </div>
            <button
              onClick={handleNextPair}
              className="w-full bg-green-600 text-white font-extrabold py-4 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight text-lg"
            >
              Continue learning
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="w-full bg-white text-gray-500 font-bold py-3 rounded-2xl border border-gray-200 hover:border-gray-300 text-sm"
            >
              Save and exit
            </button>
          </div>
        )}
      </div>
    </>
  )
}
