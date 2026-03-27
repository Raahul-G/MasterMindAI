import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import LoadingSpinner from '../components/LoadingSpinner'
import { getKnowledgeMap, backfillRecommendations } from '../api/learning'
import type { KnowledgeDomain, TopicEdge, TopicNode } from '../types'

interface LineCoord {
  x1: number
  y1: number
  x2: number
  y2: number
  cp1x: number
  cp1y: number
  cp2x: number
  cp2y: number
  sameDomain: boolean
  type: string
}

export default function KnowledgeMap() {
  const [domains, setDomains] = useState<KnowledgeDomain[]>([])
  const [edges, setEdges] = useState<TopicEdge[]>([])
  const [lines, setLines] = useState<LineCoord[]>([])
  const [loading, setLoading] = useState(true)
  const [backfilling, setBackfilling] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const containerRef = useRef<HTMLDivElement>(null)
  const nodeRefs = useRef<Record<string, HTMLDivElement | null>>({})

  const load = async () => {
    try {
      const { data } = await getKnowledgeMap()
      setDomains(data.domains)
      setEdges(data.edges)
      setLoading(false)

      const needsBackfill = data.domains.some(
        (d) =>
          d.nodes.some((n) => n.status === 'learned') &&
          !d.nodes.some((n) => n.status === 'recommended')
      )

      if (needsBackfill) {
        setBackfilling(true)
        try {
          await backfillRecommendations()
          const { data: refreshed } = await getKnowledgeMap()
          setDomains(refreshed.domains)
          setEdges(refreshed.edges)
        } catch {
          // backfill failed silently
        } finally {
          setBackfilling(false)
        }
      }
    } catch {
      setError('Failed to load knowledge map.')
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useLayoutEffect(() => {
    const container = containerRef.current
    if (!container || edges.length === 0) return

    const cRect = container.getBoundingClientRect()

    const computed: LineCoord[] = edges.flatMap((edge) => {
      const srcEl = nodeRefs.current[edge.source_id]
      const tgtEl = nodeRefs.current[edge.target_id]
      if (!srcEl || !tgtEl) return []

      const s = srcEl.getBoundingClientRect()
      const t = tgtEl.getBoundingClientRect()

      const srcDomain = srcEl.closest('[data-domain]')?.getAttribute('data-domain')
      const tgtDomain = tgtEl.closest('[data-domain]')?.getAttribute('data-domain')
      const sameDomain = srcDomain === tgtDomain

      if (sameDomain) {
        // Vertical arrow: bottom-center of source → top-center of target
        const x1 = s.left + s.width / 2 - cRect.left
        const y1 = s.bottom - cRect.top
        const x2 = t.left + t.width / 2 - cRect.left
        const y2 = t.top - cRect.top
        const mid = (y1 + y2) / 2
        return [{ x1, y1, x2, y2, cp1x: x1, cp1y: mid, cp2x: x2, cp2y: mid, sameDomain: true, type: edge.relationship_type }]
      } else {
        // Horizontal bezier: right-center of source → left-center of target
        const x1 = s.right - cRect.left
        const y1 = s.top + s.height / 2 - cRect.top
        const x2 = t.left - cRect.left
        const y2 = t.top + t.height / 2 - cRect.top
        const cpOffset = Math.abs(x2 - x1) * 0.4
        return [{ x1, y1, x2, y2, cp1x: x1 + cpOffset, cp1y: y1, cp2x: x2 - cpOffset, cp2y: y2, sameDomain: false, type: edge.relationship_type }]
      }
    })

    setLines(computed)
  }, [domains, edges])

  const handleStartRecommended = (node: TopicNode) => {
    navigate('/learn/start', {
      state: { topic: node.canonical_name },
    })
  }

  const allNodes = domains.flatMap((d) => d.nodes)

  return (
    <>
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-10">
        <h1 className="text-3xl font-extrabold text-gray-900 mb-1">Knowledge Map</h1>
        <p className="text-gray-400 mb-8 text-sm">Your learning history and what to unlock next.</p>

        {loading && <LoadingSpinner />}
        {error && <p className="text-red-500 text-sm">{error}</p>}

        {backfilling && (
          <div className="flex items-center gap-3 text-sm text-purple-600 bg-purple-50 border border-purple-200 rounded-xl px-4 py-3 mb-6">
            <svg className="animate-spin h-4 w-4 text-purple-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            Generating your recommendations...
          </div>
        )}

        {!loading && !error && allNodes.length === 0 && (
          <div className="text-center py-20 text-gray-400">
            <p className="text-5xl mb-4">🗺️</p>
            <p className="text-lg font-semibold text-gray-600 mb-2">Your map is empty</p>
            <p className="text-sm mb-6">Complete a module to unlock your knowledge graph.</p>
            <Link
              to="/learn/start"
              className="inline-block bg-green-600 text-white font-bold px-6 py-3 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75"
            >
              Start Learning
            </Link>
          </div>
        )}

        {allNodes.length > 0 && (
          <div className="relative" ref={containerRef}>
            {/* SVG overlay for arrows */}
            <svg
              style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'visible' }}
              width="100%"
              height="100%"
            >
              <defs>
                <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
                  <path d="M0,0 L0,6 L8,3 z" fill="#a855f7" />
                </marker>
                <marker id="arrow-green" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
                  <path d="M0,0 L0,6 L8,3 z" fill="#22c55e" />
                </marker>
              </defs>
              {lines.map((l, i) =>
                l.sameDomain ? (
                  <line
                    key={i}
                    x1={l.x1}
                    y1={l.y1}
                    x2={l.x2}
                    y2={l.y2}
                    stroke="#a855f7"
                    strokeWidth="2"
                    markerEnd="url(#arrow)"
                  />
                ) : (
                  <path
                    key={i}
                    d={`M${l.x1},${l.y1} C${l.cp1x},${l.cp1y} ${l.cp2x},${l.cp2y} ${l.x2},${l.y2}`}
                    stroke="#22c55e"
                    strokeWidth="1.5"
                    strokeDasharray="6 3"
                    fill="none"
                    markerEnd="url(#arrow-green)"
                  />
                )
              )}
            </svg>

            {/* Domain columns */}
            <div className="flex flex-col md:flex-row gap-8">
              {domains.map((domain) => (
                <div
                  key={domain.name}
                  data-domain={domain.name}
                  className="flex-1 min-w-0"
                >
                  <h2 className="text-base font-bold text-gray-700 mb-4 flex items-center gap-2">
                    <span className="text-purple-500">📚</span> {domain.name}
                  </h2>
                  <div className="flex flex-col gap-3">
                    {domain.nodes.map((node) => (
                      <NodeCard
                        key={node.id}
                        node={node}
                        refCallback={(el) => { nodeRefs.current[node.id] = el }}
                        onStart={handleStartRecommended}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  )
}

function NodeCard({
  node,
  refCallback,
  onStart,
}: {
  node: TopicNode
  refCallback: (el: HTMLDivElement | null) => void
  onStart: (node: TopicNode) => void
}) {
  if (node.status === 'in_progress') {
    return (
      <div
        ref={refCallback}
        className="flex items-start gap-3 bg-gray-50 border border-gray-300 rounded-xl px-4 py-3"
      >
        <span className="text-gray-400 text-lg mt-0.5">○</span>
        <div>
          <p className="font-semibold text-gray-500 text-sm">{node.display_name}</p>
          <p className="text-xs text-gray-400">In progress</p>
        </div>
      </div>
    )
  }

  if (node.status === 'learned') {
    return (
      <div
        ref={refCallback}
        className="flex items-start gap-3 bg-green-50 border border-green-200 rounded-xl px-4 py-3"
      >
        <span className="text-green-500 text-lg mt-0.5">✓</span>
        <div>
          <p className="font-semibold text-green-800 text-sm">{node.display_name}</p>
          {node.source_module_id && (
            <Link
              to={`/modules/${node.source_module_id}/review`}
              className="text-xs text-green-600 hover:underline"
            >
              Review module
            </Link>
          )}
        </div>
      </div>
    )
  }

  // recommended
  return (
    <div
      ref={refCallback}
      className="flex items-start gap-3 bg-purple-50 border border-purple-200 rounded-xl px-4 py-3"
    >
      <span className="text-purple-400 text-lg mt-0.5">→</span>
      <div className="flex-1">
        <p className="font-semibold text-purple-800 text-sm">{node.display_name}</p>
        {node.reason && (
          <p className="text-xs text-purple-600 mt-0.5">{node.reason}</p>
        )}
        {node.concept_hints && node.concept_hints.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5">
            {node.concept_hints.map((hint, i) => (
              <span key={i} className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
                {hint}
              </span>
            ))}
          </div>
        )}
        <button
          onClick={() => onStart(node)}
          className="mt-2 text-xs font-bold bg-purple-600 text-white px-3 py-1.5 rounded-lg border-b-2 border-purple-700 hover:bg-purple-700 active:translate-y-[1px] active:border-b-[1px] transition-[transform,border-bottom-width] duration-75"
        >
          Start Learning
        </button>
      </div>
    </div>
  )
}
