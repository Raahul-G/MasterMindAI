interface Props {
  question: string
  options: string[]
  selected: string | null
  onSelect: (option: string) => void
}

export default function QuizCard({ question, options, selected, onSelect }: Props) {
  return (
    <div className="bg-white rounded-2xl border-2 border-gray-200 p-6">
      <p className="text-lg font-extrabold text-forest-900 mb-6 tracking-tight">{question}</p>
      <div className="flex flex-col gap-3">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onSelect(opt)}
            className={`w-full text-left px-4 py-3 rounded-2xl border-2 font-bold transition-[border,background-color] duration-75
              ${selected === opt
                ? 'border-green-600 border-b-4 bg-green-50 text-green-700'
                : 'border-gray-200 hover:border-green-400 text-gray-700'}`}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  )
}
