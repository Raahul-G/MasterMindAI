export interface User {
  id: string
  email: string
  full_name: string
  avatar_url: string | null
  interest_topics: string[] | null
  is_active: boolean
  notion_connected: boolean
  notion_workspace_name: string | null
}

export interface Passage {
  id: string
  concept_title: string
  summary: string | null
  content: string
  use_cases: string | null
  order_index: number
  status: string
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

export interface StartModuleResponse {
  module_id: string
  eli5_text: string
  current_passage: Passage
  quiz_id: string
  questions: Question[]
  concepts_learned: number
}

export interface SubmitQuizResponse {
  score: number
  total: number
  passed: boolean
  failed_concepts: string[]
  next_passage: Passage | null
  next_quiz_id: string | null
  next_questions: Question[]
  needs_new_pair: boolean
  concepts_learned: number
}

export interface GenerateQuizResponse {
  quiz_id: string
  questions: Question[]
}

export interface NextPairResponse {
  current_passage: Passage
  quiz_id: string
  questions: Question[]
  concepts_learned: number
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
  concepts_learned: number
  eli5_text: string | null
  completed_at: string | null
  created_at: string
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
  total_concepts: number
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
  completed_at: string | null
  passages: Passage[]
  quiz_score: number | null
  quiz_total: number | null
  quiz_attempts: number | null
  questions: ReviewQuestion[]
}
