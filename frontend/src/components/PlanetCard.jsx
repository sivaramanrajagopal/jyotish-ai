const PLANET_SYMBOLS = {
  Sun: '☉', Moon: '☽', Mars: '♂', Mercury: '☿',
  Jupiter: '♃', Venus: '♀', Saturn: '♄', Rahu: '☊', Ketu: '☋',
}

const SIGN_COLORS = {
  Aries: 'text-red-400', Taurus: 'text-green-400', Gemini: 'text-yellow-300',
  Cancer: 'text-blue-300', Leo: 'text-orange-400', Virgo: 'text-emerald-400',
  Libra: 'text-pink-300', Scorpio: 'text-red-500', Sagittarius: 'text-purple-400',
  Capricorn: 'text-gray-400', Aquarius: 'text-cyan-400', Pisces: 'text-indigo-300',
}

export default function PlanetCard({ planet, data }) {
  const symbol = PLANET_SYMBOLS[planet] || '✦'
  const signColor = SIGN_COLORS[data.sign] || 'text-white'

  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex flex-col gap-1 hover:bg-white/10 transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-2xl">{symbol}</span>
        {data.retrograde && (
          <span className="text-xs text-red-400 font-medium bg-red-400/10 px-2 py-0.5 rounded-full">R</span>
        )}
      </div>
      <div className="font-semibold text-white text-sm">{planet}</div>
      <div className={`font-medium text-sm ${signColor}`}>{data.sign}</div>
      <div className="text-xs text-white/50">{data.degree_in_sign?.toFixed(1)}°  H{data.house}</div>
      <div className="text-xs text-white/40 truncate">{data.nakshatra} P{data.pada}</div>
    </div>
  )
}
