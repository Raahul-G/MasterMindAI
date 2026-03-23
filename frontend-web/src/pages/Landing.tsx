import { Link } from 'react-router-dom'

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-yellow-50 flex flex-col items-center justify-center px-6">
      <div className="max-w-2xl text-center">
        <div className="text-6xl mb-6">🧠</div>
        <h1 className="text-5xl font-extrabold text-gray-900 mb-4 leading-tight">
          Learn anything.<br />
          <span className="text-indigo-600">Master it.</span>
        </h1>
        <p className="text-xl text-gray-500 mb-10">
          AI-powered adaptive learning that teaches you until you get it. Step by step, concept by concept.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            to="/register"
            className="bg-indigo-600 text-white font-semibold px-8 py-3 rounded-xl hover:bg-indigo-700 transition-colors text-lg"
          >
            Get Started
          </Link>
          <Link
            to="/login"
            className="bg-white text-indigo-600 font-semibold px-8 py-3 rounded-xl border-2 border-indigo-200 hover:border-indigo-400 transition-colors text-lg"
          >
            Log In
          </Link>
        </div>
        <div className="mt-16 grid grid-cols-3 gap-6 text-center">
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <div className="text-3xl mb-2">📖</div>
            <p className="font-semibold text-gray-800">Adaptive Lessons</p>
            <p className="text-sm text-gray-400 mt-1">Passages tailored to your level</p>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <div className="text-3xl mb-2">✅</div>
            <p className="font-semibold text-gray-800">Smart Quizzes</p>
            <p className="text-sm text-gray-400 mt-1">Identifies exactly what you missed</p>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <div className="text-3xl mb-2">🔥</div>
            <p className="font-semibold text-gray-800">Daily Streaks</p>
            <p className="text-sm text-gray-400 mt-1">Build the habit of learning</p>
          </div>
        </div>
      </div>
    </div>
  )
}
