import axiosClient from './axiosClient'
import type { StartModuleResponse, GenerateQuizResponse, QuizResult, Remediation, AnswerSubmission } from '../types'

export const startModule = (topic: string, level: string) =>
  axiosClient.post<StartModuleResponse>('/learn/start', { topic, level })

export const generateQuiz = (module_id: string) =>
  axiosClient.post<GenerateQuizResponse>('/learn/quiz/generate', { module_id })

export const submitQuiz = (quiz_id: string, answers: AnswerSubmission[]) =>
  axiosClient.post<QuizResult>('/learn/quiz/submit', { quiz_id, answers })

export const remediate = (module_id: string, quiz_id: string, failed_concepts: string[]) =>
  axiosClient.post<{ remediations: Remediation[] }>('/learn/remediate', { module_id, quiz_id, failed_concepts })
