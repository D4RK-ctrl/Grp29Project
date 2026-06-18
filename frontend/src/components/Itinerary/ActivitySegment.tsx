import { MapPin, UtensilsCrossed, Train, Clock, ExternalLink } from 'lucide-react'
import { TripEvent, EventType } from '../../types/itinerary'

const TYPE_CONFIG: Record<EventType, { icon: React.ReactNode; color: string; bg: string; label: string }> = {
  activity: {
    icon: <MapPin className="w-3.5 h-3.5 text-white" />,
    color: 'text-purple-400',
    bg: 'bg-purple-600',
    label: 'Activity',
  },
  restaurant: {
    icon: <UtensilsCrossed className="w-3.5 h-3.5 text-white" />,
    color: 'text-orange-400',
    bg: 'bg-orange-600',
    label: 'Dining',
  },
  transport: {
    icon: <Train className="w-3.5 h-3.5 text-white" />,
    color: 'text-slate-400',
    bg: 'bg-slate-600',
    label: 'Transport',
  },
  flight_arrival: {
    icon: <MapPin className="w-3.5 h-3.5 text-white" />,
    color: 'text-blue-400',
    bg: 'bg-blue-600',
    label: 'Flight',
  },
  flight_departure: {
    icon: <MapPin className="w-3.5 h-3.5 text-white" />,
    color: 'text-blue-400',
    bg: 'bg-blue-600',
    label: 'Flight',
  },
  hotel_checkin: {
    icon: <MapPin className="w-3.5 h-3.5 text-white" />,
    color: 'text-green-400',
    bg: 'bg-green-600',
    label: 'Hotel',
  },
  hotel_checkout: {
    icon: <MapPin className="w-3.5 h-3.5 text-white" />,
    color: 'text-green-400',
    bg: 'bg-green-600',
    label: 'Hotel',
  },
}

interface Props {
  event: TripEvent
}

export default function ActivitySegment({ event }: Props) {
  const cfg = TYPE_CONFIG[event.type] ?? TYPE_CONFIG.activity

  return (
    <div className="flex gap-4 py-2 relative">
      <div className="relative z-10 w-10 h-10 flex-shrink-0 flex items-center justify-center">
        <div className={`w-8 h-8 ${cfg.bg} rounded-full flex items-center justify-center`}>
          {cfg.icon}
        </div>
      </div>

      <div className="flex-1 bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`${cfg.color} text-xs font-medium uppercase tracking-wide`}>
                {cfg.label}
              </span>
              <span className="text-slate-500 text-xs">{event.time}</span>
              {event.end_time && (
                <span className="text-slate-600 text-xs">→ {event.end_time}</span>
              )}
              {event.price_per_person !== undefined && event.price_per_person > 0 && (
                <span className="text-slate-500 text-xs ml-auto">₹{event.price_per_person}/person</span>
              )}
            </div>
            <p className="text-white font-semibold mt-0.5">{event.title}</p>
            <p className="text-slate-400 text-sm mt-1 leading-relaxed">{event.description}</p>
            {event.address && (
              <p className="text-slate-500 text-xs mt-1">{event.address}</p>
            )}
            {event.notes && (
              <p className="text-slate-500 text-xs mt-1 italic">{event.notes}</p>
            )}
          </div>
          {event.booking_url && (
            <a
              href={event.booking_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 flex-shrink-0"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>
    </div>
  )
}
