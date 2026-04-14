import { useEffect, useRef, useState } from 'react'
import ForceGraph3D from 'react-force-graph-3d'
import Navbar from '../components/Navbar'
import { getGraph } from '../api/graph'
import { useGraphStore } from '../store/graphStore'
import type { GraphNode } from '../types'

interface MappedNode {
  id: string
  label: string
  fx: number
  fy: number
  fz: number
  val: number
  color: string
}

export default function KnowledgeGraph() {
  const [mappedNodes, setMappedNodes] = useState<MappedNode[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const setHasNewNodes = useGraphStore((s) => s.setHasNewNodes)
  const containerRef = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState({ width: window.innerWidth, height: window.innerHeight })

  useEffect(() => {
    setHasNewNodes(false)
    getGraph()
      .then((res) => {
        const nodes: MappedNode[] = res.nodes
          .filter((n: GraphNode) => n.pos_x !== null)
          .map((n: GraphNode) => ({
            id: n.id,
            label: n.label,
            fx: n.pos_x as number,
            fy: n.pos_y as number,
            fz: n.pos_z as number,
            val: Math.max(1, n.hub_score * 1.5),
            color: n.hub_score > 1 ? '#4ade80' : '#16a34a',
          }))
        setMappedNodes(nodes)
      })
      .catch(() => setError('Failed to load your knowledge graph. Please try again.'))
      .finally(() => setLoading(false))
  }, [setHasNewNodes])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => {
      setSize({ width: entry.contentRect.width, height: entry.contentRect.height })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  return (
    <div className="h-screen bg-gray-950 flex flex-col overflow-hidden">
      <Navbar />
      <div ref={containerRef} className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-green-500 text-sm">Loading your knowledge graph...</p>
          </div>
        )}

        {!loading && error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {!loading && !error && mappedNodes.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
            <p className="text-green-700 text-5xl">🌱</p>
            <p className="text-gray-400 text-sm text-center max-w-xs">
              Complete your first concept to grow your knowledge map.
            </p>
          </div>
        )}

        {!loading && !error && mappedNodes.length > 0 && (
          <ForceGraph3D
            graphData={{ nodes: mappedNodes as object[], links: [] }}
            width={size.width}
            height={size.height}
            nodeVal="val"
            nodeColor="color"
            nodeLabel="label"
            backgroundColor="#030712"
          />
        )}

        {!loading && !error && mappedNodes.length > 0 && (
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-gray-900/80 text-green-400 text-sm font-semibold px-4 py-2 rounded-full border border-green-900 pointer-events-none">
            {mappedNodes.length} concept{mappedNodes.length !== 1 ? 's' : ''}
          </div>
        )}
      </div>
    </div>
  )
}
