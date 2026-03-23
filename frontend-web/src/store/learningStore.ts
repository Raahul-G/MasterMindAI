import { create } from 'zustand'
import type { Passage, Question, QuizResult, Remediation } from '../types'

interface LearningState {
  moduleId: string | null
  topic: string | null
  level: string | null
  eli5Text: string | null
  passages: Passage[]
  quizId: string | null
  questions: Question[]
  quizResult: QuizResult | null
  remediations: Remediation[]
  setModule: (moduleId: string, topic: string, level: string, eli5Text: string, passages: Passage[]) => void
  setQuiz: (quizId: string, questions: Question[]) => void
  setQuizResult: (result: QuizResult) => void
  setRemediations: (remediations: Remediation[]) => void
  reset: () => void
}

export const useLearningStore = create<LearningState>((set) => ({
  moduleId: null, topic: null, level: null, eli5Text: null,
  passages: [], quizId: null, questions: [], quizResult: null, remediations: [],
  setModule: (moduleId, topic, level, eli5Text, passages) =>
    set({ moduleId, topic, level, eli5Text, passages }),
  setQuiz: (quizId, questions) => set({ quizId, questions }),
  setQuizResult: (result) => set({ quizResult: result }),
  setRemediations: (remediations) => set({ remediations }),
  reset: () => set({
    moduleId: null, topic: null, level: null, eli5Text: null,
    passages: [], quizId: null, questions: [], quizResult: null, remediations: [],
  }),
}))
