import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plane, MapPin, Calendar, Users, Sparkles, ArrowRight } from 'lucide-react'
import { useTrip } from '../hooks/useTrip'

const EXAMPLES = [
  'I want to plan a 7-day trip to Bangkok for 2 people in July. Budget around $4000. We love temples, street food, and nightlife. Flying from New York.',
  'Plan a 5-day Paris trip for a couple in September. Budget $5000. We want romantic restaurants, museums, and day trip to Versailles. Flying from London.',
  'Family trip to Tokyo for 4 people (2 adults, 2 kids) in August, 10 days, $8000 budget. Flying from Sydney. Kids love anime and theme parks.',
]

export default function Home() {
  const [brief, setBrief] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { createTrip, error } = useTrip()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!brief.trim()) return
    setIsSubmitting(true)
    const trip = await createTrip(brief)
    if (trip) navigate(`/trip/${trip.id}`)
    setIsSubmitting(false)
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Nav */}
      <nav className="border-b border-slate-800 px-6 py-4 flex items-center gap-3">
        <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
          <Plane className="w-4 h-4 text-white" />
        </div>
        <span className="font-semibold text-white text-lg">TripAgent</span>
        <span className="ml-auto text-xs text-slate-500">AI-Powered Travel Planning</span>
      </nav>

      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-16">
        <div className="max-w-2xl w-full space-y-8">
          <div className="text-center space-y-4">
            <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 text-blue-400 text-sm">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Multi-tool AI agent — real flight & hotel data</span>
            </div>
            <h1 className="text-5xl font-bold text-white leading-tight">
              Brief it once.<br />
              <span className="text-blue-400">It plans everything.</span>
            </h1>
            <p className="text-slate-400 text-lg">
              Describe your trip in plain English. The agent searches real flights, hotels,
              activities and restaurants — then assembles a complete day-by-day itinerary.
            </p>
          </div>

          {/* Features */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { icon: <Plane className="w-4 h-4" />, label: 'Real flights', sub: 'via Amadeus' },
              { icon: <MapPin className="w-4 h-4" />, label: 'Live hotels', sub: 'via Amadeus' },
              { icon: <Sparkles className="w-4 h-4" />, label: 'Conflict-free', sub: 'auto-resolved' },
            ].map((f) => (
              <div key={f.label} className="bg-slate-900 border border-slate-800 rounded-xl p-3 text-center">
                <div className="text-blue-400 flex justify-center mb-1">{f.icon}</div>
                <div className="text-white text-sm font-medium">{f.label}</div>
                <div className="text-slate-500 text-xs">{f.sub}</div>
              </div>
            ))}
          </div>

          {/* Input form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <textarea
                value={brief}
                onChange={(e) => setBrief(e.target.value)}
                placeholder="Describe your trip: destination, dates, budget, travellers, preferences..."
                rows={4}
                className="w-full bg-slate-900 border border-slate-700 rounded-2xl px-5 py-4 text-white placeholder-slate-500 resize-none focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors text-sm"
              />
              <div className="absolute bottom-3 right-3 flex items-center gap-2">
                <span className="text-slate-600 text-xs">{brief.length} chars</span>
              </div>
            </div>

            {error && (
              <div className="bg-red-900/30 border border-red-700 rounded-xl px-4 py-3 text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={!brief.trim() || isSubmitting}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold py-3.5 rounded-2xl transition-colors flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Starting agent...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Plan my trip
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Example briefs */}
          <div className="space-y-2">
            <p className="text-slate-500 text-xs uppercase tracking-wider">Try an example</p>
            <div className="space-y-2">
              {EXAMPLES.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => setBrief(ex)}
                  className="w-full text-left bg-slate-900/50 hover:bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-slate-400 hover:text-slate-300 text-sm transition-colors"
                >
                  {ex.slice(0, 100)}...
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
