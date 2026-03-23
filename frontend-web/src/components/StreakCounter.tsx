interface Props { current: number; longest: number }

export default function StreakCounter({ current, longest }: Props) {
  return (
    <div className="flex items-center gap-2 bg-orange-50 border border-orange-200 rounded-xl px-4 py-2">
      <span className="text-2xl">🔥</span>
      <div>
        <p className="text-lg font-bold text-orange-600">{current} day streak</p>
        <p className="text-xs text-gray-400">Best: {longest} days</p>
      </div>
    </div>
  )
}
