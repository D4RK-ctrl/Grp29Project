import { Plane, Calendar, Users, IndianRupee, Sun, MapPin } from 'lucide-react'
import { Itinerary } from '../../types/itinerary'

interface Props {
  itinerary: Itinerary
}

export default function TripSummary({ itinerary }: Props) {
  const { summary, flights, accommodation, weather } = itinerary

  const fmt = (date: string) =>
    new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

  return (
    <div className="space-y-4">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-bold text-white">
          {summary.origin} → {summary.destination}
        </h1>
        <p className="text-slate-400 mt-1">
          {fmt(summary.departure_date)} – {fmt(summary.return_date)} · {summary.duration_days} days · {summary.travellers} traveller{summary.travellers > 1 ? 's' : ''}
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          icon={<IndianRupee className="w-4 h-4 text-green-400" />}
          label="Est. Total"
          value={`₹${summary.estimated_total_cost?.toLocaleString() ?? '—'}`}
          sub={`Budget: ₹${summary.budget_total?.toLocaleString() ?? '—'}`}
          color="green"
        />
        <StatCard
          icon={<Plane className="w-4 h-4 text-blue-400" />}
          label="Flights"
          value={`₹${flights?.outbound?.total_price?.toLocaleString() ?? '—'}`}
          sub={`${flights?.outbound?.airline ?? ''} · ${flights?.outbound?.stops ?? 0} stop(s)`}
          color="blue"
        />
        <StatCard
          icon={<MapPin className="w-4 h-4 text-purple-400" />}
          label="Hotel"
          value={accommodation?.name?.split(' ').slice(0, 2).join(' ') ?? '—'}
          sub={`₹${accommodation?.price_per_night ?? '—'}/night · ${accommodation?.rating ?? '—'}★`}
          color="purple"
        />
        <StatCard
          icon={<Sun className="w-4 h-4 text-yellow-400" />}
          label="Weather"
          value={weather?.summary?.split(',')[0] ?? '—'}
          sub={weather?.advice?.slice(0, 40) ?? ''}
          color="yellow"
        />
      </div>

      {/* Visa & tips */}
      {(itinerary.visa_info || itinerary.travel_tips?.length > 0) && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3">
          {itinerary.visa_info && (
            <div className="text-sm">
              <span className="text-slate-500 uppercase tracking-wider text-xs">Visa</span>
              <p className="text-slate-300 mt-1">{itinerary.visa_info}</p>
            </div>
          )}
          {itinerary.travel_tips?.length > 0 && (
            <div className="text-sm">
              <span className="text-slate-500 uppercase tracking-wider text-xs">Travel Tips</span>
              <ul className="mt-1 space-y-1">
                {itinerary.travel_tips.map((tip, i) => (
                  <li key={i} className="text-slate-400 flex gap-2">
                    <span className="text-blue-500">·</span>{tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function StatCard({
  icon, label, value, sub, color,
}: {
  icon: React.ReactNode
  label: string
  value: string
  sub: string
  color: string
}) {
  const bg: Record<string, string> = {
    green: 'border-green-800/30',
    blue: 'border-blue-800/30',
    purple: 'border-purple-800/30',
    yellow: 'border-yellow-800/30',
  }
  return (
    <div className={`bg-slate-900 border ${bg[color] ?? 'border-slate-800'} rounded-2xl p-4`}>
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-slate-500 text-xs uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-white font-semibold truncate">{value}</p>
      <p className="text-slate-500 text-xs mt-0.5 truncate">{sub}</p>
    </div>
  )
}
