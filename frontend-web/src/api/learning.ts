import axiosClient from './axiosClient'
import type { StartModuleResponse, GenerateQuizResponse, QuizResult, Remediation, AnswerSubmission } from '../types'

export const startModule = (topic: string, level: string) =>
  axiosClient.post<StartModuleResponse>('/learn/start', { topic, level })

export const generateQuiz = (module_id: string) =>
  axiosClient.post<GenerateQuizResponse>('/learn/quiz/generate', { module_id })

export const submitQuiz = (quiz_id: string, answers: AnswerSubmission[]) => {
  const d = new Date()
  const local_date = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  return axiosClient.post<QuizResult>('/learn/quiz/submit', { quiz_id, answers, local_date })
}

export const remediate = (module_id: string, quiz_id: string, failed_concepts: string[]) =>
  axiosClient.post<{ remediations: Remediation[] }>('/learn/remediate', { module_id, quiz_id, failed_concepts })
