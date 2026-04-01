interface Props { current: number; longest: number }

const TIERS = [
  { days: 365, name: 'Aurora', isViolet: true },
  { days: 350, name: 'Summit', isViolet: true },
  { days: 300, name: 'Valley', isViolet: true },
  { days: 250, name: 'Meadow', isViolet: true },
  { days: 200, name: 'River',  isViolet: true },
  { days: 150, name: 'Ridge',  isViolet: true },
  { days: 100, name: 'Peak',   isViolet: true },
  { days: 90,  name: 'Cloud',  isViolet: true },
  { days: 60,  name: 'Star',   isViolet: true },
  { days: 30,  name: 'Moon',   isViolet: true },
  { days: 21,  name: 'Sun',    isViolet: false },
  { days: 14,  name: 'Rain',   isViolet: false },
  { days: 7,   name: 'Mist',   isViolet: false },
  { days: 3,   name: 'Dew',    isViolet: false },
]

export default function StreakCounter({ current, longest }: Props) {
  const tier = TIERS.find((t) => current >= t.days) ?? null
  const isViolet = tier?.isViolet ?? false

  return (
    <div className={`flex items-center gap-2 rounded-xl px-4 py-2 border ${
      isViolet
        ? 'bg-purple-50 border-purple-200'
        : 'bg-green-50 border-green-200'
    }`}>
      <span className="text-2xl">{isViolet ? '🌙' : '🔥'}</span>
      <div>
        <p className={`text-lg font-extrabold ${isViolet ? 'text-purple-700' : 'text-green-700'}`}>
          {tier ? `${tier.name} · ` : ''}{current} day{current !== 1 ? 's' : ''}
        </p>
        <p className="text-xs text-gray-400">Best: {longest} days</p>
      </div>
    </div>
  )
}
