import { useState } from 'react'
import { Send, Loader2, RefreshCw } from 'lucide-react'

const PRESETS = [
  'My outbound flight was cancelled — find alternatives',
  'Change hotel to something cheaper',
  'Add a day trip on day 3',
  'Move the trip one week later',
]

interface Props {
  onSubmit: (text: string) => void
  isLoading: boolean
}

export default function ChangeRequest({ onSubmit, isLoading }: Props) {
  const [text, setText] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim() || isLoading) return
    onSubmit(text.trim())
    setText('')
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
        <span className="text-slate-500 text-xs uppercase tracking-wider">Request a change</span>
      </div>

      {/* Quick presets */}
      <div className="flex flex-wrap gap-1.5">
        {PRESETS.map((p) => (
          <button
            key={p}
            onClick={() => setText(p)}
            className="text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-400 hover:text-slate-300 rounded-lg px-2.5 py-1 transition-colors"
          >
            {p.slice(0, 28)}…
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Describe your change..."
          disabled={isLoading}
          className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-white placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!text.trim() || isLoading}
          className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white rounded-xl px-3 py-2.5 transition-colors"
        >
          {isLoading
            ? <Loader2 className="w-4 h-4 animate-spin" />
            : <Send className="w-4 h-4" />
          }
        </button>
      </form>
    </div>
  )
}
