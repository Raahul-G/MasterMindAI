interface Props { emoji: string; name: string; description: string; locked?: boolean }

export default function AchievementBadge({ emoji, name, description, locked }: Props) {
  return (
    <div className={`flex items-center gap-3 rounded-xl p-3 border transition-all ${
      locked
        ? 'bg-gray-50 border-gray-100 opacity-40 grayscale'
        : 'bg-green-50 border-purple-200'
    }`}>
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
        locked ? 'bg-gray-100' : 'bg-green-100 ring-2 ring-purple-200'
      }`}>
        <span className="text-2xl">{emoji}</span>
      </div>
      <div>
        <p className={`font-bold text-sm ${locked ? 'text-gray-400' : 'text-purple-700'}`}>{name}</p>
        <p className={`text-xs ${locked ? 'text-gray-300' : 'text-green-700'}`}>{description}</p>
      </div>
    </div>
  )
}
