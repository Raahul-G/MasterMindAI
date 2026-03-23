import axiosClient from './axiosClient'
import type { Streak, Achievement } from '../types'

export const getStreak = () => axiosClient.get<Streak>('/gamification/streak')
export const getAchievements = () => axiosClient.get<Achievement[]>('/gamification/achievements')
