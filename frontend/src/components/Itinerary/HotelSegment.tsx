import { Hotel } from 'lucide-react'
import { TripEvent } from '../../types/itinerary'

interface Props {
  event: TripEvent
}

export default function HotelSegment({ event }: Props) {
  const isCheckin = event.type === 'hotel_checkin'

  return (
    <div className="flex gap-4 py-2 relative">
      <div className="relative z-10 w-10 h-10 flex-shrink-0 flex items-center justify-center">
        <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
          <Hotel className="w-3.5 h-3.5 text-white" />
        </div>
      </div>

      <div className="flex-1 bg-green-900/20 border border-green-800/30 rounded-xl px-4 py-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-green-400 text-xs font-medium uppercase tracking-wide">
                {isCheckin ? 'Check-In' : 'Check-Out'}
              </span>
              <span className="text-slate-500 text-xs">{event.time}</span>
            </div>
            <p className="text-white font-semibold mt-0.5">{event.title}</p>
            <p className="text-slate-400 text-sm mt-1">{event.description}</p>
            {event.address && (
              <p className="text-slate-500 text-xs mt-1">{event.address}</p>
            )}
            {event.notes && (
              <p className="text-slate-500 text-xs mt-1 italic">{event.notes}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
