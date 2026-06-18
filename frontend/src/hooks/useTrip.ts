import { useState } from 'react'
import axios from 'axios'
import { Trip } from '../types/itinerary'

const API = import.meta.env.VITE_API_URL || 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://travel-agent-backend-b986.onrender.com')

export function useTrip() {
  const [trip, setTrip] = useState<Trip | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createTrip = async (brief: string): Promise<Trip | null> => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await axios.post<Trip>(`${API}/api/trips`, { brief })
      setTrip(data)
      return data
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to create trip')
      return null
    } finally {
      setLoading(false)
    }
  }

  const fetchTrip = async (tripId: string): Promise<Trip | null> => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await axios.get<Trip>(`${API}/api/trips/${tripId}`)
      setTrip(data)
      return data
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to fetch trip')
      return null
    } finally {
      setLoading(false)
    }
  }

  const requestChange = async (tripId: string, changeRequest: string): Promise<Trip | null> => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await axios.post<Trip>(`${API}/api/trips/${tripId}/change`, {
        change_request: changeRequest,
      })
      setTrip(data)
      return data
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to process change')
      return null
    } finally {
      setLoading(false)
    }
  }

  return { trip, setTrip, loading, error, createTrip, fetchTrip, requestChange }
}
