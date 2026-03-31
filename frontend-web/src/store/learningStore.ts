import { create } from 'zustand'
import type { Passage, Question, StartModuleResponse } from '../types'

interface LearningState {
  moduleId: string | null
  eli5Text: string | null
  currentPassage: Passage | null
  quizId: string | null
  questions: Question[]
  conceptsLearned: number
  setStart: (data: StartModuleResponse) => void
  setPassage: (passage: Passage, quizId: string, questions: Question[], conceptsLearned: number) => void
  setConceptsLearned: (n: number) => void
  reset: () => void
}

export const useLearningStore = create<LearningState>((set) => ({
  moduleId: null,
  eli5Text: null,
  currentPassage: null,
  quizId: null,
  questions: [],
  conceptsLearned: 0,

  setStart: (data) =>
    set({
      moduleId: data.module_id,
      eli5Text: data.eli5_text,
      currentPassage: data.current_passage,
      quizId: data.quiz_id,
      questions: data.questions,
      conceptsLearned: data.concepts_learned,
    }),

  setPassage: (passage, quizId, questions, conceptsLearned) =>
    set({ currentPassage: passage, quizId, questions, conceptsLearned }),

  setConceptsLearned: (n) => set({ conceptsLearned: n }),

  reset: () =>
    set({
      moduleId: null,
      eli5Text: null,
      currentPassage: null,
      quizId: null,
      questions: [],
      conceptsLearned: 0,
    }),
}))
