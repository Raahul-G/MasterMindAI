import axios from 'axios'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type { TokenResponse } from '../types'

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

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

axiosClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableConfig

    if (error.response?.status === 401 && !originalRequest._retry) {
      // Don't redirect for auth endpoints — 401 there means wrong credentials, not expired session
      const url = originalRequest.url ?? ''
      if (url.includes('/auth/login') || url.includes('/auth/register')) {
        return Promise.reject(error)
      }

      const refreshToken = localStorage.getItem('refresh_token')

      if (refreshToken) {
        originalRequest._retry = true
        try {
          const { data } = await axiosClient.post<TokenResponse>('/auth/refresh', {
            refresh_token: refreshToken,
          })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          return axiosClient(originalRequest)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(error)
        }
      }

      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }

    return Promise.reject(error)
  }
)

export default axiosClient
