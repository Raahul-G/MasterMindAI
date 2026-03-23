import axiosClient from './axiosClient'
import type { Module, ModuleDetail } from '../types'

export const getModules = () =>
  axiosClient.get<Module[]>('/modules')

export const getModule = (id: string) =>
  axiosClient.get<ModuleDetail>(`/modules/${id}`)

export const exportDownload = (id: string) =>
  axiosClient.post<{ download_url: string }>(`/modules/${id}/export/download`)

export const exportNotion = (id: string) =>
  axiosClient.post<{ notion_page_url: string }>(`/modules/${id}/export/notion`)
