import { useState, useEffect, useRef } from 'react'
import { StreamMessage } from '../types/itinerary'

const WS_URL = import.meta.env.VITE_WS_URL || 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'ws://localhost:8000'
    : 'wss://travel-agent-backend-b986.onrender.com')

export type StreamStatus = 'idle' | 'connecting' | 'running' | 'complete' | 'error'

export function useAgentStream(tripId: string | null) {
  const [messages, setMessages] = useState<StreamMessage[]>([])
  const [status, setStatus] = useState<StreamStatus>('idle')
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!tripId) return

    setStatus('connecting')
    setMessages([])

    const ws = new WebSocket(`${WS_URL}/api/trips/${tripId}/stream`)
    wsRef.current = ws

    ws.onopen = () => setStatus('running')

    ws.onmessage = (event) => {
      const msg: StreamMessage = JSON.parse(event.data)
      if (msg.type === 'heartbeat') return
      setMessages((prev) => [...prev, msg])
      if (msg.type === 'complete') setStatus('complete')
      if (msg.type === 'error') setStatus('error')
    }

    ws.onerror = () => setStatus('error')
    ws.onclose = () => {
      if (status !== 'complete' && status !== 'error') {
        setStatus('idle')
      }
    }

    return () => {
      ws.close()
    }
  }, [tripId])

  return { messages, status }
}
