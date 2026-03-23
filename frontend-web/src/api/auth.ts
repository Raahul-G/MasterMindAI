import axiosClient from './axiosClient'
import type { User } from '../types'

export const register = (email: string, password: string, full_name: string) =>
  axiosClient.post<{ access_token: string }>('/auth/register', { email, password, full_name })

export const login = (email: string, password: string) =>
  axiosClient.post<{ access_token: string }>('/auth/login', { email, password })

export const getMe = () =>
  axiosClient.get<User>('/auth/me')

export const googleLogin = (id_token: string) =>
  axiosClient.post<{ access_token: string }>('/auth/google', { id_token })

export const updateInterests = (interest_topics: string[]) =>
  axiosClient.put<User>('/auth/interests', { interest_topics })
