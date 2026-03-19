import { useStore } from '../../store'

function formatTime(ms: number): string {
  const s = Math.floor(ms / 1000)
  const m = Math.floor(s / 60)
  const h = Math.floor(m / 60)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${pad(h)}:${pad(m % 60)}:${pad(s % 60)}`
}

interface Props {
  timestamp: number | null
  label: string
  description: string
}

export function ProtocolCard({ timestamp, label, description }: Props) {
  const setSeekTo = useStore((s) => s.setSeekTo)

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-blue-500 transition-colors">
      <div className="flex items-start justify-between mb-1">
        <span className="text-sm font-medium text-white">{label}</span>
        {timestamp !== null && (
          <button
            onClick={() => setSeekTo(timestamp)}
            className="text-xs text-blue-400 hover:text-blue-300 shrink-0 ml-2"
          >
            {formatTime(timestamp)}
          </button>
        )}
      </div>
      {description && <p className="text-xs text-gray-400">{description}</p>}
    </div>
  )
}
