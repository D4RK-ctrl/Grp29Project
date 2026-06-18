export type EventType =
  | 'flight_arrival'
  | 'flight_departure'
  | 'hotel_checkin'
  | 'hotel_checkout'
  | 'activity'
  | 'restaurant'
  | 'transport'

export interface TripEvent {
  id: string
  time: string
  end_time?: string
  type: EventType
  title: string
  description: string
  location?: string
  address?: string
  price_per_person?: number
  booking_required?: boolean
  booking_url?: string
  notes?: string
}

export interface TripDay {
  date: string
  day_number: number
  theme: string
  events: TripEvent[]
}

export interface FlightSegment {
  airline: string
  flight_number: string
  origin: string
  destination: string
  departure_time: string
  arrival_time: string
  duration: string
  stops: number
  stop_details?: string
  price_per_person: number
  total_price: number
  cabin_class: string
  booking_url?: string
}

export interface Accommodation {
  name: string
  address: string
  city: string
  checkin_date: string
  checkin_time: string
  checkout_date: string
  checkout_time: string
  rating: number
  price_per_night: number
  total_price: number
  amenities: string[]
  booking_url?: string
}

export interface WeatherDay {
  date: string
  temp_high: number
  temp_low: number
  description: string
  humidity?: number
}

export interface Conflict {
  day: string
  type: string
  event1: string
  event1_end: string
  event2: string
  event2_start: string
  description: string
}

export interface Itinerary {
  summary: {
    origin: string
    origin_code: string
    destination: string
    destination_code: string
    departure_date: string
    return_date: string
    duration_days: number
    travellers: number
    budget_total: number
    estimated_total_cost: number
    currency: string
  }
  flights: {
    outbound: FlightSegment
    return?: FlightSegment
  }
  accommodation: Accommodation
  days: TripDay[]
  weather: {
    summary: string
    advice?: string
    daily: WeatherDay[]
  }
  conflicts: Conflict[]
  travel_tips: string[]
  visa_info?: string
  changes_summary?: {
    change_request: string
    changes_made: string[]
    conflicts_resolved: string[]
  }
}

export interface Trip {
  id: string
  brief: string
  status: 'planning' | 'complete' | 'failed'
  itinerary?: Itinerary
  created_at: string
}

export interface StreamMessage {
  type: 'status' | 'tool_call' | 'tool_result' | 'complete' | 'error' | 'heartbeat'
  message?: string
  tool?: string
  summary?: string
  itinerary?: Itinerary
}
