import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Plane, ArrowLeft } from 'lucide-react'
import { useTrip } from '../hooks/useTrip'
import { useAgentStream } from '../hooks/useAgentStream'
import AgentThinking from '../components/Chat/AgentThinking'
import TripSummary from '../components/Dashboard/TripSummary'
import ConflictBanner from '../components/Dashboard/ConflictBanner'
import ChangeRequest from '../components/Dashboard/ChangeRequest'
import TimelineView from '../components/Itinerary/TimelineView'

export default function TripDashboard() {
  const { tripId } = useParams<{ tripId: string }>()
  const navigate = useNavigate()
  const { trip, setTrip, fetchTrip, requestChange } = useTrip()
  const { messages, status } = useAgentStream(
    trip?.status === 'planning' || !trip?.itinerary ? tripId ?? null : null
  )
  const [changePending, setChangePending] = useState(false)
  const [changeStreamId, setChangeStreamId] = useState<string | null>(null)

  // Load trip on mount
  useEffect(() => {
    if (tripId) fetchTrip(tripId)
  }, [tripId])

  // Poll for completion when status is planning
  useEffect(() => {
    if (trip?.status !== 'planning') return
    const interval = setInterval(async () => {
      if (tripId) {
        const updated = await fetchTrip(tripId)
        if (updated?.status !== 'planning') clearInterval(interval)
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [trip?.status, tripId])

  const handleChangeRequest = async (text: string) => {
    if (!tripId) return
    setChangePending(true)
    setChangeStreamId(tripId)
    await requestChange(tripId, text)
    setChangePending(false)
    setChangeStreamId(null)
  }

  const isPlanning = trip?.status === 'planning'
  const itinerary = trip?.itinerary

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Nav */}
      <nav className="border-b border-slate-800 px-6 py-4 flex items-center gap-4 sticky top-0 bg-slate-950 z-10">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          New trip
        </button>
        <div className="flex items-center gap-2 ml-auto">
          <div className="w-6 h-6 bg-blue-500 rounded-md flex items-center justify-center">
            <Plane className="w-3 h-3 text-white" />
          </div>
          <span className="font-semibold text-white">TripAgent</span>
        </div>
        {itinerary && (
          <span className="text-slate-400 text-sm">
            {itinerary.summary.destination} · {itinerary.summary.duration_days} days
          </span>
        )}
      </nav>

      <div className="flex-1 flex overflow-hidden">
        {/* Left: Agent thinking + change chat */}
        <aside className="w-96 border-r border-slate-800 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4">
            <AgentThinking
              messages={messages}
              status={status}
              isPlanning={isPlanning}
              brief={trip?.brief}
            />
          </div>
          {itinerary && (
            <div className="border-t border-slate-800 p-4">
              <ChangeRequest onSubmit={handleChangeRequest} isLoading={changePending} />
            </div>
          )}
        </aside>

        {/* Right: Itinerary */}
        <main className="flex-1 overflow-y-auto">
          {isPlanning && !itinerary ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center space-y-4">
                <div className="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto" />
                <p className="text-slate-400 text-lg">Agent is building your itinerary...</p>
                <p className="text-slate-600 text-sm">This usually takes 30–60 seconds</p>
              </div>
            </div>
          ) : itinerary ? (
            <div className="p-6 space-y-6 max-w-4xl mx-auto">
              <TripSummary itinerary={itinerary} />
              {itinerary.conflicts?.length > 0 && (
                <ConflictBanner conflicts={itinerary.conflicts} />
              )}
              {itinerary.changes_summary && (
                <div className="bg-emerald-900/20 border border-emerald-700/50 rounded-2xl p-5">
                  <h3 className="text-emerald-400 font-semibold mb-3">Changes Applied</h3>
                  <ul className="space-y-1">
                    {itinerary.changes_summary.changes_made.map((c, i) => (
                      <li key={i} className="text-slate-300 text-sm flex gap-2">
                        <span className="text-emerald-500 mt-0.5">✓</span>
                        {c}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <TimelineView days={itinerary.days} />
            </div>
          ) : trip?.status === 'failed' ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center space-y-4">
                <p className="text-red-400 text-lg">Agent failed to generate itinerary.</p>
                <button
                  onClick={() => navigate('/')}
                  className="text-blue-400 hover:underline text-sm"
                >
                  Try again with a different brief
                </button>
              </div>
            </div>
          ) : null}
        </main>
      </div>
    </div>
  )
}
