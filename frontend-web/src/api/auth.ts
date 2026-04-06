import axiosClient from './axiosClient'
import type { User, TokenResponse } from '../types'

export const register = (email: string, password: string, full_name: string) =>
  axiosClient.post<TokenResponse>('/auth/register', { email, password, full_name })

export const login = (email: string, password: string) =>
  axiosClient.post<TokenResponse>('/auth/login', { email, password })

export const getMe = () =>
  axiosClient.get<User>('/auth/me')

export const googleLogin = (id_token: string) =>
  axiosClient.post<TokenResponse>('/auth/google', { id_token })

export const refreshTokens = (refresh_token: string) =>
  axiosClient.post<TokenResponse>('/auth/refresh', { refresh_token })

export const logout = () =>
  axiosClient.post('/auth/logout')

export const updateInterests = (interest_topics: string[]) =>
  axiosClient.put<User>('/auth/interests', { interest_topics })
