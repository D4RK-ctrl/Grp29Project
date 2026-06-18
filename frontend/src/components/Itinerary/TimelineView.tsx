import { TripDay } from '../../types/itinerary'
import DayCard from './DayCard'

interface Props {
  days: TripDay[]
}

export default function TimelineView({ days }: Props) {
  return (
    <div className="space-y-2">
      <h2 className="text-xl font-bold text-white">Day-by-Day Itinerary</h2>
      <div className="space-y-4">
        {days.map((day) => (
          <DayCard key={day.date} day={day} />
        ))}
      </div>
    </div>
  )
}
