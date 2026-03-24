interface Props { current: number; total: number }

export default function ProgressBar({ current, total }: Props) {
  const pct = Math.round((current / total) * 100)
  return (
    <div className="w-full bg-gray-200 rounded-full h-5 overflow-hidden">
      <div
        className="relative bg-green-600 h-5 rounded-full transition-all duration-300 overflow-hidden"
        style={{ width: `${pct}%` }}
      >
        {/* Shine overlay — semi-transparent white line across top */}
        <div className="absolute top-[3px] left-2 right-2 h-[3px] rounded-full bg-white opacity-30" />
      </div>
    </div>
  )
}
