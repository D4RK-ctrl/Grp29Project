import { AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { Conflict } from '../../types/itinerary'

interface Props {
  conflicts: Conflict[]
}

export default function ConflictBanner({ conflicts }: Props) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-amber-900/20 border border-amber-700/50 rounded-2xl overflow-hidden">
      <button
        className="w-full flex items-center gap-3 px-5 py-4 text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
        <div className="flex-1">
          <span className="text-amber-400 font-semibold">
            {conflicts.length} Scheduling Conflict{conflicts.length > 1 ? 's' : ''} Detected
          </span>
          <p className="text-amber-600 text-xs mt-0.5">
            The agent identified and logged these — use the change chat to resolve.
          </p>
        </div>
        {expanded
          ? <ChevronUp className="w-4 h-4 text-amber-500" />
          : <ChevronDown className="w-4 h-4 text-amber-500" />
        }
      </button>

      {expanded && (
        <div className="border-t border-amber-800/40 px-5 py-3 space-y-3">
          {conflicts.map((c, i) => (
            <div key={i} className="text-sm">
              <div className="text-amber-300 font-medium">{c.day}</div>
              <div className="text-amber-600 mt-0.5">{c.description}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
