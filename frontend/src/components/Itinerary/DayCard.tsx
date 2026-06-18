import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { TripDay } from '../../types/itinerary'
import FlightSegment from './FlightSegment'
import HotelSegment from './HotelSegment'
import ActivitySegment from './ActivitySegment'

interface Props {
  day: TripDay
}

export default function DayCard({ day }: Props) {
  const [open, setOpen] = useState(true)

  const fmt = (date: string) =>
    new Date(date + 'T00:00:00').toLocaleDateString('en-US', {
      weekday: 'long', month: 'long', day: 'numeric',
    })

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
      <button
        className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-slate-800/30 transition-colors"
        onClick={() => setOpen(!open)}
      >
        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
          {day.day_number}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-white font-semibold">{fmt(day.date)}</p>
          <p className="text-slate-400 text-sm truncate">{day.theme}</p>
        </div>
        <span className="text-slate-500 text-xs">{day.events?.length ?? 0} events</span>
        {open
          ? <ChevronUp className="w-4 h-4 text-slate-600 flex-shrink-0" />
          : <ChevronDown className="w-4 h-4 text-slate-600 flex-shrink-0" />
        }
      </button>

      {open && day.events?.length > 0 && (
        <div className="border-t border-slate-800 px-5 py-4">
          {/* Vertical timeline */}
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-[19px] top-0 bottom-0 w-px bg-slate-800" />

            <div className="space-y-1">
              {day.events.map((event, i) => {
                const isLast = i === day.events.length - 1
                if (event.type === 'flight_arrival' || event.type === 'flight_departure') {
                  return <FlightSegment key={event.id} event={event} />
                }
                if (event.type === 'hotel_checkin' || event.type === 'hotel_checkout') {
                  return <HotelSegment key={event.id} event={event} />
                }
                return <ActivitySegment key={event.id} event={event} />
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
