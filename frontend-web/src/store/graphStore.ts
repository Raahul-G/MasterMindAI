import { create } from 'zustand'

interface GraphStore {
  hasNewNodes: boolean
  setHasNewNodes: (v: boolean) => void
}

export const useGraphStore = create<GraphStore>((set) => ({
  hasNewNodes: false,
  setHasNewNodes: (v) => set({ hasNewNodes: v }),
}))
