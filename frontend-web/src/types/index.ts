export interface User {
  id: string
  email: string
  full_name: string
  avatar_url: string | null
  interest_topics: string[] | null
  is_active: boolean
}

export interface Passage {
  id: string
  concept_title: string
  content: string
  order_index: number
}

export interface Question {
  id: string
  concept_title: string
  question_text: string
  question_type: 'true_false' | 'multiple_choice'
  options: string[]
  order_index: number
}

export interface AnswerSubmission {
  question_id: string
  user_answer: string
}

export interface QuizResult {
  score: number
  total: number
  passed: boolean
  failed_concepts: string[]
}

export interface Remediation {
  concept_title: string
  content: string
}

export interface Module {
  id: string
  topic: string
  level: 'kid' | 'intermediate' | 'expert'
  status: 'in_progress' | 'completed'
  eli5_text: string | null
  completed_at: string | null
  created_at: string
}

export interface ModuleDetail extends Module {
  passages: Passage[]
}

export interface StartModuleResponse {
  module_id: string
  eli5_text: string
  passages: Passage[]
}

export interface GenerateQuizResponse {
  quiz_id: string
  questions: Question[]
}

export interface Achievement {
  slug: string
  name: string
  description: string
  icon_emoji: string
  earned_at: string
}

export interface Streak {
  current_streak: number
  longest_streak: number
  last_activity_date: string | null
}

export interface FriendResponse {
  id: string
  full_name: string
  avatar_url: string | null
  current_streak: number
}

export interface FriendRequestResponse {
  id: string
  requester: { id: string; full_name: string; avatar_url: string | null }
  created_at: string
}

export interface ActivityFeedItem {
  id: string
  user: { id: string; full_name: string; avatar_url: string | null }
  activity_type: 'module_completed' | 'achievement_earned'
  metadata: Record<string, unknown>
  created_at: string
}

export interface UserSearchResult {
  id: string
  full_name: string
  avatar_url: string | null
}

export interface ReviewQuestion {
  question_text: string
  concept_title: string
  options: string[]
  correct_answer: string
  user_answer: string | null
  is_correct: boolean | null
}

export interface ModuleReview {
  id: string
  topic: string
  level: string
  eli5_text: string
  status: string
  passages: Passage[]
  quiz_score: number | null
  quiz_total: number | null
  quiz_attempts: number | null
  questions: ReviewQuestion[]
}
