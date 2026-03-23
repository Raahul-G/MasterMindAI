interface Props {
  question: string
  options: string[]
  selected: string | null
  onSelect: (option: string) => void
}

export default function QuizCard({ question, options, selected, onSelect }: Props) {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-6">
      <p className="text-lg font-semibold text-gray-800 mb-6">{question}</p>
      <div className="flex flex-col gap-3">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onSelect(opt)}
            className={`w-full text-left px-4 py-3 rounded-xl border-2 transition-all
              ${selected === opt
                ? 'border-indigo-500 bg-indigo-50 text-indigo-700 font-medium'
                : 'border-gray-200 hover:border-indigo-300 text-gray-700'}`}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  )
}
