interface Props {
  totalConcepts: number
}

const TIERS = [
  { name: 'Seed',   threshold: 1,   fill: '#BBF7D0', textClass: 'text-purple-700' },
  { name: 'Sprout', threshold: 25,  fill: '#71E01A', textClass: 'text-purple-700' },
  { name: 'Leaf',   threshold: 50,  fill: '#58CC02', textClass: 'text-purple-700' },
  { name: 'Tree',   threshold: 75,  fill: '#46A302', textClass: 'text-purple-600' },
  { name: 'Forest', threshold: 100, fill: '#14532D', textClass: 'text-purple-400' },
] as const

function getMasteryState(totalConcepts: number) {
  if (totalConcepts <= 0) return { level: 1, withinLevel: 0, fillPct: 0, tier: TIERS[0] }
  const level = Math.floor((totalConcepts - 1) / 100) + 1
  const withinLevel = ((totalConcepts - 1) % 100) + 1
  const fillPct = withinLevel // each concept = 1%
  const tier = [...TIERS].reverse().find((t) => withinLevel >= t.threshold) ?? TIERS[0]
  return { level, withinLevel, fillPct, tier }
}

export default function MasteryBar({ totalConcepts }: Props) {
  const { level, fillPct, tier } = getMasteryState(totalConcepts)

  const tierLabel = level > 1 ? `Lv.${level} ${tier.name}` : tier.name
  const nextTier = TIERS[TIERS.findIndex((t) => t.name === tier.name) + 1]

  return (
    <div>
      {/* Labels row */}
      <div className="flex items-baseline justify-between mb-2">
        <span className="font-extrabold text-purple-700 text-base">{tierLabel}</span>
        <span className="text-xs text-purple-500 font-semibold">
          {totalConcepts} concept{totalConcepts !== 1 ? 's' : ''} learned
          {nextTier && ` · ${nextTier.threshold + (level - 1) * 100 - totalConcepts} to ${nextTier.name}`}
        </span>
      </div>

      {/* Bar */}
      <div className="relative h-7 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 rounded-full transition-[width] duration-700 ease-out"
          style={{ width: `${fillPct}%`, backgroundColor: tier.fill }}
        />
        {/* Milestone marker lines at 25%, 50%, 75% */}
        {[25, 50, 75].map((pct) => (
          <div
            key={pct}
            className="absolute top-0 h-full w-px bg-white/50 pointer-events-none"
            style={{ left: `${pct}%` }}
          />
        ))}
      </div>

      {/* Tier name labels below the bar */}
      <div className="flex justify-between mt-1.5 px-0.5">
        {TIERS.map((t) => {
          const withinLevel = totalConcepts > 0 ? ((totalConcepts - 1) % 100) + 1 : 0
          const reached = withinLevel >= t.threshold
          return (
            <span
              key={t.name}
              className={`text-xs font-semibold transition-colors ${
                reached ? 'text-purple-700' : 'text-gray-300'
              }`}
            >
              {t.name}
            </span>
          )
        })}
      </div>
    </div>
  )
}
