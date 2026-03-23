import { create } from 'zustand'
import type { User } from '../types'

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
