import axiosClient from './axiosClient'

export const getNotionAuthUrl = () =>
  axiosClient.get<{ url: string }>('/notion/auth-url')

export const getNotionStatus = () =>
  axiosClient.get<{ connected: boolean; workspace_name: string | null }>('/notion/status')

export const disconnectNotion = () =>
  axiosClient.delete<{ message: string }>('/notion/disconnect')
