interface Props { emoji: string; name: string; description: string; locked?: boolean }

export default function AchievementBadge({ emoji, name, description, locked }: Props) {
  return (
    <div className={`flex items-center gap-3 rounded-xl p-3 border ${
      locked
        ? 'bg-gray-50 border-gray-100 opacity-50 grayscale'
        : 'bg-green-50 border-green-200'
    }`}>
      <span className="text-3xl">{emoji}</span>
      <div>
        <p className={`font-semibold text-sm ${locked ? 'text-gray-500' : 'text-forest-900'}`}>{name}</p>
        <p className={`text-xs ${locked ? 'text-gray-400' : 'text-green-700'}`}>{description}</p>
      </div>
    </div>
  )
}
