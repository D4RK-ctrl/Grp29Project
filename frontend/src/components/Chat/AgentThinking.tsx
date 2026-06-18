import { useRef, useEffect } from 'react'
import { Plane, Hotel, MapPin, UtensilsCrossed, Cloud, Search, CheckCircle, AlertCircle, Loader2, Bot } from 'lucide-react'
import { StreamMessage } from '../../types/itinerary'
import { StreamStatus } from '../../hooks/useAgentStream'

const TOOL_ICONS: Record<string, React.ReactNode> = {
  search_flights: <Plane className="w-3.5 h-3.5" />,
  search_hotels: <Hotel className="w-3.5 h-3.5" />,
  search_activities: <MapPin className="w-3.5 h-3.5" />,
  search_restaurants: <UtensilsCrossed className="w-3.5 h-3.5" />,
  get_weather: <Cloud className="w-3.5 h-3.5" />,
  web_search: <Search className="w-3.5 h-3.5" />,
}

const TOOL_COLORS: Record<string, string> = {
  search_flights: 'text-blue-400 bg-blue-500/10',
  search_hotels: 'text-green-400 bg-green-500/10',
  search_activities: 'text-purple-400 bg-purple-500/10',
  search_restaurants: 'text-orange-400 bg-orange-500/10',
  get_weather: 'text-cyan-400 bg-cyan-500/10',
  web_search: 'text-yellow-400 bg-yellow-500/10',
}

interface Props {
  messages: StreamMessage[]
  status: StreamStatus
  isPlanning: boolean
  brief?: string
}

export default function AgentThinking({ messages, status, isPlanning, brief }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 bg-blue-500/20 rounded-lg flex items-center justify-center">
          <Bot className="w-4 h-4 text-blue-400" />
        </div>
        <span className="text-slate-300 font-medium text-sm">Agent Activity</span>
        {status === 'running' && (
          <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin ml-auto" />
        )}
        {status === 'complete' && (
          <CheckCircle className="w-3.5 h-3.5 text-green-400 ml-auto" />
        )}
      </div>

      {brief && (
        <div className="bg-slate-800/50 rounded-xl p-3 text-slate-400 text-xs leading-relaxed border border-slate-700/50">
          <span className="text-slate-500 uppercase tracking-wider text-[10px]">Brief</span>
          <p className="mt-1">{brief.slice(0, 180)}{brief.length > 180 ? '...' : ''}</p>
        </div>
      )}

      {messages.length === 0 && isPlanning && (
        <div className="flex items-center gap-2 text-slate-500 text-sm py-2">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          Connecting to agent...
        </div>
      )}

      <div className="space-y-2">
        {messages.map((msg, i) => {
          if (msg.type === 'status') {
            return (
              <div key={i} className="flex items-start gap-2 text-slate-400 text-sm py-1">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
                {msg.message}
              </div>
            )
          }

          if (msg.type === 'tool_call') {
            const colorClass = TOOL_COLORS[msg.tool || ''] || 'text-slate-400 bg-slate-500/10'
            const icon = TOOL_ICONS[msg.tool || ''] || <Search className="w-3.5 h-3.5" />
            return (
              <div key={i} className={`flex items-start gap-2 rounded-lg px-3 py-2 ${colorClass}`}>
                <span className="mt-0.5 flex-shrink-0">{icon}</span>
                <span className="text-xs leading-relaxed">{msg.message}</span>
                <Loader2 className="w-3 h-3 animate-spin ml-auto flex-shrink-0 mt-0.5 opacity-60" />
              </div>
            )
          }

          if (msg.type === 'tool_result') {
            const colorClass = TOOL_COLORS[msg.tool || ''] || 'text-slate-400 bg-slate-500/10'
            return (
              <div key={i} className="flex items-start gap-2 text-slate-500 text-xs pl-2 py-1 border-l-2 border-slate-700">
                <CheckCircle className="w-3 h-3 text-green-500 mt-0.5 flex-shrink-0" />
                <span>{msg.summary}</span>
              </div>
            )
          }

          if (msg.type === 'complete') {
            return (
              <div key={i} className="flex items-center gap-2 bg-green-900/20 border border-green-700/30 rounded-lg px-3 py-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-green-400 text-sm font-medium">Itinerary ready</span>
              </div>
            )
          }

          if (msg.type === 'error') {
            return (
              <div key={i} className="flex items-center gap-2 bg-red-900/20 border border-red-700/30 rounded-lg px-3 py-2">
                <AlertCircle className="w-4 h-4 text-red-400" />
                <span className="text-red-400 text-sm">{msg.message}</span>
              </div>
            )
          }

          return null
        })}
      </div>

      <div ref={bottomRef} />
    </div>
  )
}
