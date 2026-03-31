interface Props {
  title: string
  summary?: string | null
  content: string
  use_cases?: string | null
  index: number
  revised?: boolean
}

export default function PassageCard({ title, summary, content, use_cases, index, revised }: Props) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded-full">
          Concept {index + 1}
        </span>
        {revised && (
          <span className="bg-yellow-100 text-yellow-700 text-xs font-bold px-2 py-1 rounded-full">
            Revised
          </span>
        )}
        <h3 className="font-bold text-gray-800">{title}</h3>
      </div>

      {/* Flashcard summary */}
      {summary && (
        <div className="bg-purple-50 border border-purple-100 rounded-xl px-4 py-3 mb-4 flex gap-2 items-start">
          <span className="text-purple-400 font-bold text-sm mt-0.5">💡</span>
          <p className="text-purple-800 font-medium text-sm leading-relaxed">{summary}</p>
        </div>
      )}

      {/* Explanation */}
      <p className="text-gray-600 leading-relaxed text-sm mb-4">{content}</p>

      {/* Use cases */}
      {use_cases && (
        <div className="border-t border-gray-100 pt-4">
          <p className="text-xs font-bold text-gray-400 uppercase tracking-wide mb-1">Where it's used</p>
          <p className="text-gray-500 text-sm leading-relaxed">{use_cases}</p>
        </div>
      )}
    </div>
  )
}
