import { useEffect, useState } from 'react'

interface Thought { icon: string; text: string }

interface Props {
  thoughts: Thought[]
  intervalMs?: number
}

export default function ThinkingCard({ thoughts, intervalMs = 2000 }: Props) {
  const [index, setIndex] = useState(0)
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const timer = setInterval(() => {
      setVisible(false)
      const swap = setTimeout(() => {
        setIndex((i) => (i + 1) % thoughts.length)
        setVisible(true)
      }, 300)
      return () => clearTimeout(swap)
    }, intervalMs)
    return () => clearInterval(timer)
  }, [thoughts.length, intervalMs])

  const thought = thoughts[index]

  return (
    <div className="bg-white border-2 border-gray-100 rounded-2xl p-10 flex flex-col items-center text-center gap-3">
      <div
        className="flex flex-col items-center gap-3 transition-opacity duration-300"
        style={{ opacity: visible ? 1 : 0 }}
      >
        <span className="text-5xl leading-none">{thought.icon}</span>
        <p className="text-base font-medium text-gray-500">{thought.text}</p>
      </div>
      <div className="flex gap-1.5 mt-4">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2 h-2 rounded-full bg-green-400 animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  )
}
