import axiosClient from './axiosClient'
import type { Module, ModuleReview } from '../types'

export const getModules = () =>
  axiosClient.get<Module[]>('/modules')

export const getModuleReview = (id: string) =>
  axiosClient.get<ModuleReview>(`/modules/${id}/review`)
