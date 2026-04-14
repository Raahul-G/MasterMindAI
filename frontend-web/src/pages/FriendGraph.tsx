import { useEffect, useRef, useState } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import ForceGraph3D from 'react-force-graph-3d'
import Navbar from '../components/Navbar'
import { getFriendGraph } from '../api/graph'
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

export default function FriendGraph() {
  const { userId } = useParams<{ userId: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const friendName: string = (location.state as { friendName?: string } | null)?.friendName ?? 'Friend'

  const [mappedNodes, setMappedNodes] = useState<MappedNode[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState({ width: window.innerWidth, height: window.innerHeight })

  useEffect(() => {
    if (!userId) return
    getFriendGraph(userId)
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
      .catch((err) => {
        const status = err?.response?.status
        if (status === 403) {
          setError('You are not friends with this user.')
        } else {
          setError('Failed to load this graph. Please try again.')
        }
      })
      .finally(() => setLoading(false))
  }, [userId])

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

      {/* Header bar */}
      <div className="flex items-center gap-3 px-5 py-3 bg-gray-900 border-b border-gray-800">
        <button
          onClick={() => navigate('/friends')}
          className="text-green-500 hover:text-green-400 text-sm font-semibold"
        >
          ← Back
        </button>
        <span className="text-gray-500 text-sm">|</span>
        <span className="text-white text-sm font-semibold">{friendName}'s Knowledge Graph</span>
        {!loading && !error && (
          <span className="ml-auto text-green-600 text-xs font-medium">
            {mappedNodes.length} concept{mappedNodes.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <div ref={containerRef} className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-green-500 text-sm">Loading graph...</p>
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
              {friendName} hasn't completed any concepts yet.
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
      </div>
    </div>
  )
}
