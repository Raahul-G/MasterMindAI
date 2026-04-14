import axiosClient from './axiosClient'
import type { GraphResponse } from '../types'

export const getGraph = async (): Promise<GraphResponse> => {
  const { data } = await axiosClient.get<GraphResponse>('/graph')
  return data
}

export const populateGraph = async (): Promise<{ populated: number }> => {
  const { data } = await axiosClient.post<{ populated: number }>('/graph/populate')
  return data
}

export const getFriendGraph = async (friendUserId: string): Promise<GraphResponse> => {
  const { data } = await axiosClient.get<GraphResponse>(`/graph/friend/${friendUserId}`)
  return data
}
