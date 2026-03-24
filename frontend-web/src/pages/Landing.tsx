import { Link } from 'react-router-dom'

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-yellow-50 flex flex-col items-center justify-center px-6">
      <div className="max-w-2xl text-center">
        <div className="text-6xl mb-6">🧠</div>
        <h1 className="text-5xl font-extrabold text-forest-900 mb-4 leading-tight">
          Learn anything.<br />
          <span className="text-green-600">Master it.</span>
        </h1>
        <p className="text-xl text-gray-500 mb-10">
          AI-powered adaptive learning that teaches you until you get it. Step by step, concept by concept.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            to="/register"
            className="bg-green-600 text-white font-extrabold px-8 py-3 rounded-2xl border-b-4 border-green-700 hover:bg-green-700 active:translate-y-[2px] active:border-b-2 transition-[transform,border-bottom-width] duration-75 tracking-tight text-lg"
          >
            Get Started
          </Link>
          <Link
            to="/login"
            className="bg-white text-green-600 font-semibold px-8 py-3 rounded-xl border-2 border-green-200 hover:border-green-500 transition-colors text-lg"
          >
            Log In
          </Link>
        </div>
        <div className="mt-16 grid grid-cols-3 gap-6 text-center">
          <div className="bg-white rounded-2xl p-5 border-2 border-gray-200">
            <div className="text-3xl mb-2">📖</div>
            <p className="font-semibold text-gray-800">Adaptive Lessons</p>
            <p className="text-sm text-gray-400 mt-1">Passages tailored to your level</p>
          </div>
          <div className="bg-white rounded-2xl p-5 border-2 border-gray-200">
            <div className="text-3xl mb-2">✅</div>
            <p className="font-semibold text-gray-800">Smart Quizzes</p>
            <p className="text-sm text-gray-400 mt-1">Identifies exactly what you missed</p>
          </div>
          <div className="bg-white rounded-2xl p-5 border-2 border-gray-200">
            <div className="text-3xl mb-2">🔥</div>
            <p className="font-semibold text-gray-800">Daily Streaks</p>
            <p className="text-sm text-gray-400 mt-1">Build the habit of learning</p>
          </div>
        </div>
      </div>
    </div>
  )
}
