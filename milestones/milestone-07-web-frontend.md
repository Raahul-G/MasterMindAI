# Milestone 7 — Web Frontend

> **Covers:** Stage 11 (Web Frontend)
> **Status:** Not started

---

## What this milestone is

The backend is live. This milestone builds the React web app that talks to it.

The UI is Duolingo-inspired — friendly, colourful, clean. Every screen maps to a backend endpoint. The full learning flow (topic → ELI5 → passages → quiz → remediation → complete) must work end-to-end in the browser.

There are 9 chunks. The first two lay the foundation (scaffold, types, API, stores). Chunks 3–7 build the screens in the order a real user would encounter them. Chunk 8 deploys to Vercel.

**Live backend URL:** `https://mastermindai-production.up.railway.app`

---

## What you will be able to do when this milestone is done

- Register and log in via the web browser
- Pick a topic and level, read the ELI5 and passages
- Take the quiz, see results, go through remediation if needed
- See your streak and earned achievements on the profile page
- Search for friends and see the activity feed
- Access the app at a live Vercel URL

---

## The chunks

---

### Chunk 1 — Scaffold the project

**What you learn:** How Vite bootstraps a React + TypeScript project and how Tailwind is wired in.

- [ ] From the repo root:
  ```bash
  npm create vite@latest frontend-web -- --template react-ts
  cd frontend-web
  npm install
  npm install react-router-dom axios zustand
  npm install -D tailwindcss @tailwindcss/vite
  ```

- [ ] Replace `frontend-web/src/index.css` with:
  ```css
  @import "tailwindcss";
  ```

- [ ] Update `frontend-web/vite.config.ts`:
  ```ts
  import { defineConfig } from 'vite'
  import react from '@vitejs/plugin-react'
  import tailwindcss from '@tailwindcss/vite'

  export default defineConfig({
    plugins: [react(), tailwindcss()],
  })
  ```

- [ ] Create `frontend-web/.env`:
  ```env
  VITE_API_BASE_URL=https://mastermindai-production.up.railway.app
  VITE_GOOGLE_CLIENT_ID=your-google-client-id
  ```

- [ ] Replace `frontend-web/src/App.tsx` with a basic router skeleton:
  ```tsx
  import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

  export default function App() {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<div className="p-8 text-2xl font-bold text-indigo-600">MasterMind — coming soon</div>} />
        </Routes>
      </BrowserRouter>
    )
  }
  ```

- [ ] Run `npm run dev` and confirm the page loads at `http://localhost:5173`

**Outcome:** Vite dev server runs, Tailwind works (indigo text visible), router is in place.

---

### Chunk 2 — Types, API layer, and stores

**What you learn:** How to centralise all TypeScript interfaces, how to add a JWT interceptor to Axios, and how Zustand stores work.

#### `src/types/index.ts`
All interfaces in one file. No `any` anywhere.

```ts
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
```

#### `src/api/axiosClient.ts`
Single Axios instance. Reads JWT from Zustand store on every request.

```ts
import axios from 'axios'

const axiosClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
})

axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default axiosClient
```

#### `src/api/auth.ts`
```ts
import axiosClient from './axiosClient'
import { User } from '../types'

export const register = (email: string, password: string, full_name: string) =>
  axiosClient.post<{ access_token: string }>('/auth/register', { email, password, full_name })

export const login = (email: string, password: string) =>
  axiosClient.post<{ access_token: string }>('/auth/login', { email, password })

export const getMe = () =>
  axiosClient.get<User>('/auth/me')

export const updateInterests = (interest_topics: string[]) =>
  axiosClient.put<User>('/auth/interests', { interest_topics })
```

#### `src/api/learning.ts`
```ts
import axiosClient from './axiosClient'
import { StartModuleResponse, GenerateQuizResponse, QuizResult, Remediation, AnswerSubmission } from '../types'

export const startModule = (topic: string, level: string) =>
  axiosClient.post<StartModuleResponse>('/learn/start', { topic, level })

export const generateQuiz = (module_id: string) =>
  axiosClient.post<GenerateQuizResponse>('/learn/quiz/generate', { module_id })

export const submitQuiz = (quiz_id: string, answers: AnswerSubmission[]) =>
  axiosClient.post<QuizResult>('/learn/quiz/submit', { quiz_id, answers })

export const remediate = (module_id: string, quiz_id: string, failed_concepts: string[]) =>
  axiosClient.post<{ remediations: Remediation[] }>('/learn/remediate', { module_id, quiz_id, failed_concepts })
```

#### `src/api/modules.ts`
```ts
import axiosClient from './axiosClient'
import { Module, ModuleDetail } from '../types'

export const getModules = () =>
  axiosClient.get<Module[]>('/modules')

export const getModule = (id: string) =>
  axiosClient.get<ModuleDetail>(`/modules/${id}`)

export const exportDownload = (id: string) =>
  axiosClient.post<{ download_url: string }>(`/modules/${id}/export/download`)

export const exportNotion = (id: string) =>
  axiosClient.post<{ notion_page_url: string }>(`/modules/${id}/export/notion`)
```

#### `src/api/social.ts`
```ts
import axiosClient from './axiosClient'
import { FriendResponse, FriendRequestResponse, ActivityFeedItem, UserSearchResult } from '../types'

export const getFriends = () => axiosClient.get<FriendResponse[]>('/social/friends')
export const getFriendRequests = () => axiosClient.get<FriendRequestResponse[]>('/social/friends/requests')
export const sendFriendRequest = (addressee_id: string) =>
  axiosClient.post('/social/friends/request', { addressee_id })
export const acceptFriendRequest = (friendship_id: string) =>
  axiosClient.post('/social/friends/accept', { friendship_id })
export const getFeed = () => axiosClient.get<ActivityFeedItem[]>('/social/feed')
export const searchUsers = (q: string) =>
  axiosClient.get<UserSearchResult[]>('/social/users/search', { params: { q } })
```

#### `src/store/authStore.ts`
```ts
import { create } from 'zustand'
import { User } from '../types'

interface AuthState {
  user: User | null
  token: string | null
  setAuth: (token: string, user: User) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  setAuth: (token, user) => {
    localStorage.setItem('access_token', token)
    set({ token, user })
  },
  clearAuth: () => {
    localStorage.removeItem('access_token')
    set({ token: null, user: null })
  },
}))
```

#### `src/store/learningStore.ts`
```ts
import { create } from 'zustand'
import { Passage, Question, QuizResult, Remediation } from '../types'

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
```

**Outcome:** All types defined, all API functions wired, both stores ready. No UI yet.

---

### Chunk 3 — Auth pages: Landing, Login, Register

**What you learn:** How to build protected routes in React Router, and how to persist auth state across page refreshes using localStorage.

#### Shared components first

`src/components/LoadingSpinner.tsx`:
```tsx
export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
```

`src/components/Navbar.tsx`:
```tsx
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function Navbar() {
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const logout = () => { clearAuth(); navigate('/login') }

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <Link to="/dashboard" className="text-xl font-bold text-indigo-600">MasterMind</Link>
      {user && (
        <div className="flex items-center gap-4">
          <Link to="/profile" className="text-sm text-gray-600 hover:text-indigo-600">{user.full_name}</Link>
          <button onClick={logout} className="text-sm text-gray-400 hover:text-red-500">Logout</button>
        </div>
      )}
    </nav>
  )
}
```

#### Protected route wrapper

`src/components/ProtectedRoute.tsx`:
```tsx
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  return token ? <>{children}</> : <Navigate to="/login" replace />
}
```

#### Pages

`src/pages/Landing.tsx` — hero page with two CTA buttons (Login / Get Started).

Key elements:
- Large headline: "Learn anything. Master it."
- Subtext: "AI-powered adaptive learning that teaches you until you get it."
- Two buttons: `Link to="/login"` and `Link to="/register"`
- Use indigo + yellow colour palette, clean and friendly

`src/pages/Login.tsx`:
- Email + password form
- On submit: call `login()` API → `setAuth(token, user)` (fetch user with `getMe()`) → `navigate('/dashboard')`
- Link to Register at the bottom
- Show error message on failed login

`src/pages/Register.tsx`:
- Full name + email + password form
- On submit: call `register()` API → `setAuth(token, user)` → `navigate('/dashboard')`
- Link to Login at the bottom

#### Wire up App.tsx
```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
// ... import all other pages

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        {/* ... all other protected routes */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
```

**Outcome:** Can register, log in, and be redirected. Unauthenticated users redirected to `/login`.

---

### Chunk 4 — Dashboard and Topic Selection

**What you learn:** How to fetch data on page load with `useEffect`, and how to pass state between pages using the Zustand store.

#### `src/pages/Dashboard.tsx`

- Fetch `GET /modules` on mount, display a grid of module cards
- Each card shows: topic, level badge, status (in progress / completed), date
- "Start Learning" button → navigates to `/learn`
- Empty state: friendly illustration + "Start your first module" button
- Show streak counter at the top using `GET /gamification/streak`

#### `src/components/StreakCounter.tsx`
```tsx
interface Props { current: number; longest: number }

export default function StreakCounter({ current, longest }: Props) {
  return (
    <div className="flex items-center gap-2 bg-orange-50 border border-orange-200 rounded-xl px-4 py-2">
      <span className="text-2xl">🔥</span>
      <div>
        <p className="text-lg font-bold text-orange-600">{current} day streak</p>
        <p className="text-xs text-gray-400">Best: {longest} days</p>
      </div>
    </div>
  )
}
```

#### `src/pages/TopicSelection.tsx`

- Text input for topic (e.g. "Quantum mechanics")
- Three level buttons: Kid / Intermediate / Expert — highlighted when selected
- "Start Learning" button — on click:
  1. Call `startModule(topic, level)`
  2. Save response to `learningStore.setModule(...)`
  3. Navigate to `/learn`
- Show loading spinner while API call is in progress

**Outcome:** Dashboard shows past modules and streak. Topic selection starts a new module.

---

### Chunk 5 — Learning flow: Learning, Quiz, QuizResults, Remediation, ModuleComplete

**What you learn:** How to manage a multi-step flow using a single Zustand store as the source of truth across pages.

#### `src/pages/Learning.tsx`

Reads from `learningStore`. Shows:
1. ELI5 box at top — light yellow background, emoji icon, the ELI5 text
2. Passage cards below — one per concept
3. "Take the Quiz" button at the bottom

`src/components/PassageCard.tsx`:
```tsx
interface Props { title: string; content: string; index: number }

export default function PassageCard({ title, content, index }: Props) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="bg-indigo-100 text-indigo-700 text-xs font-bold px-2 py-1 rounded-full">
          Concept {index + 1}
        </span>
        <h3 className="font-semibold text-gray-800">{title}</h3>
      </div>
      <p className="text-gray-600 leading-relaxed">{content}</p>
    </div>
  )
}
```

When "Take the Quiz" is clicked:
1. Call `generateQuiz(moduleId)`
2. Save to `learningStore.setQuiz(...)`
3. Navigate to `/quiz`

#### `src/pages/Quiz.tsx`

Reads questions from `learningStore`. Shows:
- Progress bar: `question X of Y`
- One question at a time with option buttons
- "Next" button advances, last question shows "Submit"
- On submit: call `submitQuiz(quizId, answers)` → save result → navigate to `/quiz/results`

`src/components/QuizCard.tsx`:
```tsx
interface Props {
  question: string
  options: string[]
  selected: string | null
  onSelect: (option: string) => void
}

export default function QuizCard({ question, options, selected, onSelect }: Props) {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-6">
      <p className="text-lg font-semibold text-gray-800 mb-6">{question}</p>
      <div className="flex flex-col gap-3">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onSelect(opt)}
            className={`w-full text-left px-4 py-3 rounded-xl border-2 transition-all
              ${selected === opt
                ? 'border-indigo-500 bg-indigo-50 text-indigo-700 font-medium'
                : 'border-gray-200 hover:border-indigo-300 text-gray-700'}`}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  )
}
```

`src/components/ProgressBar.tsx`:
```tsx
interface Props { current: number; total: number }

export default function ProgressBar({ current, total }: Props) {
  const pct = Math.round((current / total) * 100)
  return (
    <div className="w-full bg-gray-200 rounded-full h-3">
      <div
        className="bg-indigo-500 h-3 rounded-full transition-all duration-300"
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}
```

#### `src/pages/QuizResults.tsx`

Shows score, pass/fail status, and failed concepts list.
- If `passed`: show celebration, "Complete Module" button → navigate to `/complete`
- If `failed`: show which concepts failed, "Start Remediation" button → call `remediate()` → navigate to `/remediation`

#### `src/pages/Remediation.tsx`

Shows re-explanations for each failed concept.
- Each remediation displayed as a `PassageCard` with a "revised" badge
- "Retake Quiz" button at the bottom → generate a new quiz for the same module → navigate to `/quiz`

#### `src/pages/ModuleComplete.tsx`

Celebration screen:
- "Module Complete!" heading with trophy emoji
- Summary: topic, level, score, streaks earned
- Two export buttons: "Download Markdown" (calls `exportDownload`) and "Push to Notion"
- "Back to Dashboard" button
- Show any newly earned achievement badges

`src/components/AchievementBadge.tsx`:
```tsx
interface Props { emoji: string; name: string; description: string }

export default function AchievementBadge({ emoji, name, description }: Props) {
  return (
    <div className="flex items-center gap-3 bg-yellow-50 border border-yellow-200 rounded-xl p-3">
      <span className="text-3xl">{emoji}</span>
      <div>
        <p className="font-semibold text-yellow-800">{name}</p>
        <p className="text-xs text-yellow-600">{description}</p>
      </div>
    </div>
  )
}
```

**Outcome:** Full learning loop works — topic → passages → quiz → results → remediation → complete.

---

### Chunk 6 — Profile page

**What you learn:** How to display multiple data sources (user info, streak, achievements) on a single page with parallel fetches.

#### `src/pages/Profile.tsx`

Fetch all three in parallel on mount:
```ts
const [streak, achievements] = await Promise.all([
  axiosClient.get('/gamification/streak'),
  axiosClient.get('/gamification/achievements'),
])
```

Display:
- User avatar (initials fallback) + name + email
- `StreakCounter` component
- Achievement grid — `AchievementBadge` for each earned achievement, greyed-out placeholders for unearned ones (show all 8 slugs)
- "Edit Interests" section — editable tag list for `interest_topics`, saves with `updateInterests()`

**Outcome:** Profile page shows streak, all achievements (earned + locked), and editable interests.

---

### Chunk 7 — Friends page

**What you learn:** How to build a search-and-action pattern — search, render results, trigger an action on each result.

#### `src/pages/Friends.tsx`

Three sections on one page:

1. **Search** — text input (min 2 chars), calls `searchUsers(q)` on change (debounced 300ms), shows results with "Add Friend" button on each
2. **Incoming requests** — fetched on mount with `getFriendRequests()`, "Accept" button on each
3. **Friends list** — fetched on mount with `getFriends()`, shows name + streak for each

Activity feed section at the bottom:
- Fetched with `getFeed()`
- Each item shows user avatar, activity description, and timestamp
- `module_completed` → "finished learning [topic] — [score]/[total]"
- `achievement_earned` → "earned [emoji] [name]"

**Outcome:** Full social graph — can search, request, accept, and see friend activity.

---

### Chunk 8 — Deploy to Vercel

**What you learn:** How Vercel auto-detects Vite projects and how to set environment variables for production.

- [ ] Push all frontend code to the `main` branch
- [ ] Go to https://vercel.com → New Project → Import `MasterMindAI`
- [ ] Set **Root Directory** to `frontend-web`
- [ ] Set **Framework Preset** to `Vite`
- [ ] Add environment variables:
  - `VITE_API_BASE_URL` = `https://mastermindai-production.up.railway.app`
  - `VITE_GOOGLE_CLIENT_ID` = your Google OAuth client ID
- [ ] Deploy
- [ ] Copy the Vercel URL (e.g. `https://mastermind-ai.vercel.app`)
- [ ] Go back to Railway → update `FRONTEND_URL` variable from `*` to the Vercel URL
- [ ] Go to Google Cloud Console → OAuth credentials → add the Vercel URL to **Authorised JavaScript origins**

**Outcome:** App is live at a public Vercel URL. CORS is locked to the Vercel domain.

---

### Chunk 9 — End-to-end browser test

Work through the full flow in the browser on the live Vercel URL:

- [ ] Register a new account → redirected to Dashboard
- [ ] Go to Topic Selection → enter "Black holes" at level "intermediate"
- [ ] Read ELI5 and passages on Learning page
- [ ] Take quiz → submit answers
- [ ] If failed: go through remediation → retake quiz
- [ ] Complete module → see celebration screen
- [ ] Check Profile → streak incremented, at least `first_steps` badge earned
- [ ] Search for a second user, send friend request, accept it from the other account
- [ ] Check Friends feed — see the module completion event

**Outcome:** Full app works end-to-end on production.

---

## Milestone 7 complete checklist (summary)

- [ ] Chunk 1 — Vite + Tailwind + React Router scaffolded, dev server runs
- [ ] Chunk 2 — All types, API modules, and stores written
- [ ] Chunk 3 — Landing, Login, Register pages + protected routes working
- [ ] Chunk 4 — Dashboard (module list + streak) + Topic Selection working
- [ ] Chunk 5 — Full learning flow: Learning → Quiz → Results → Remediation → Complete
- [ ] Chunk 6 — Profile page with streak, achievements, interests
- [ ] Chunk 7 — Friends page: search, requests, friends list, activity feed
- [ ] Chunk 8 — Deployed to Vercel, Railway CORS updated
- [ ] Chunk 9 — End-to-end browser test passes on live URL

---

## Before starting Milestone 8

Do not start Milestone 8 until every box above is checked AND:

- The full learning loop works on the live Vercel URL
- Profile page shows streak and achievements after completing a module
- Two users can become friends and see each other's feed

Tell Claude: "Milestone 7 is complete. Starting Milestone 8."
