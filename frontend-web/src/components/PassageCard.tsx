interface Props { title: string; content: string; index: number; revised?: boolean }

export default function PassageCard({ title, content, index, revised }: Props) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded-full">
          Concept {index + 1}
        </span>
        {revised && (
          <span className="bg-yellow-100 text-yellow-700 text-xs font-bold px-2 py-1 rounded-full">
            Revised
          </span>
        )}
        <h3 className="font-semibold text-gray-800">{title}</h3>
      </div>
      <p className="text-gray-600 leading-relaxed">{content}</p>
    </div>
  )
}
