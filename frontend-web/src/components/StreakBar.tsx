interface Props {
  currentStreak: number
  earnedSlugs: Set<string>
}

const GREEN_TIERS = [
  { days: 3,   slug: 'streak_dew_3',   name: 'Dew',  emoji: '💧' },
  { days: 7,   slug: 'streak_mist_7',  name: 'Mist', emoji: '🌫️' },
  { days: 14,  slug: 'streak_rain_14', name: 'Rain', emoji: '🌧️' },
  { days: 21,  slug: 'streak_sun_21',  name: 'Sun',  emoji: '☀️' },
]

const VIOLET_TIERS = [
  { days: 30,  slug: 'streak_moon_30',   name: 'Moon',   emoji: '🌙' },
  { days: 60,  slug: 'streak_star_60',   name: 'Star',   emoji: '⭐' },
  { days: 90,  slug: 'streak_cloud_90',  name: 'Cloud',  emoji: '☁️' },
  { days: 100, slug: 'streak_peak_100',  name: 'Peak',   emoji: '🏔️' },
  { days: 150, slug: 'streak_ridge_150', name: 'Ridge',  emoji: '🏔️' },
  { days: 200, slug: 'streak_river_200', name: 'River',  emoji: '🌊' },
  { days: 250, slug: 'streak_meadow_250',name: 'Meadow', emoji: '🌾' },
  { days: 300, slug: 'streak_valley_300',name: 'Valley', emoji: '🏞️' },
  { days: 350, slug: 'streak_summit_350',name: 'Summit', emoji: '🗻' },
  { days: 365, slug: 'streak_aurora_365',name: 'Aurora', emoji: '🌌' },
]

function TierTile({
  emoji, name, days, earned, isViolet,
}: { emoji: string; name: string; days: number; earned: boolean; isViolet: boolean }) {
  return (
    <div
      className={`flex flex-col items-center gap-0.5 rounded-xl p-2 border text-center transition-all ${
        earned
          ? isViolet
            ? 'bg-purple-50 border-purple-200'
            : 'bg-green-50 border-green-200'
          : 'bg-gray-50 border-gray-100 opacity-40 grayscale'
      }`}
    >
      <span className="text-2xl leading-none">{emoji}</span>
      <p className={`text-xs font-bold mt-0.5 ${earned ? (isViolet ? 'text-purple-700' : 'text-green-700') : 'text-gray-400'}`}>
        {name}
      </p>
      <p className={`text-[10px] ${earned ? (isViolet ? 'text-purple-400' : 'text-green-500') : 'text-gray-300'}`}>
        {days}d
      </p>
    </div>
  )
}

export default function StreakBar({ currentStreak, earnedSlugs }: Props) {
  return (
    <div>
      {/* Green tiers */}
      <p className="text-xs font-bold text-green-600 uppercase tracking-wider mb-2">Green</p>
      <div className="grid grid-cols-4 gap-2 mb-4">
        {GREEN_TIERS.map((t) => (
          <TierTile
            key={t.slug}
            emoji={t.emoji}
            name={t.name}
            days={t.days}
            earned={earnedSlugs.has(t.slug) || currentStreak >= t.days}
            isViolet={false}
          />
        ))}
      </div>

      {/* Violet tiers */}
      <p className="text-xs font-bold text-purple-600 uppercase tracking-wider mb-2">Violet</p>
      <div className="grid grid-cols-4 gap-2">
        {VIOLET_TIERS.map((t) => (
          <TierTile
            key={t.slug}
            emoji={t.emoji}
            name={t.name}
            days={t.days}
            earned={earnedSlugs.has(t.slug) || currentStreak >= t.days}
            isViolet={true}
          />
        ))}
      </div>
    </div>
  )
}
