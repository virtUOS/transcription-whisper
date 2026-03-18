import { useStore } from '../../store'
import type { SummaryChapter } from '../../api/types'

function formatTime(ms: number): string {
  const s = Math.floor(ms / 1000)
  const m = Math.floor(s / 60)
  const h = Math.floor(m / 60)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${pad(h)}:${pad(m % 60)}:${pad(s % 60)}`
}

interface Props {
  chapter: SummaryChapter
  index: number
}

export function ChapterCard({ chapter, index }: Props) {
  const setSeekTo = useStore((s) => s.setSeekTo)

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-blue-500 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm font-medium text-white">
          {index + 1}. {chapter.title}
        </h3>
        <button
          onClick={() => setSeekTo(chapter.start_time)}
          className="text-xs text-blue-400 hover:text-blue-300 shrink-0 ml-2"
        >
          {formatTime(chapter.start_time)} — {formatTime(chapter.end_time)}
        </button>
      </div>
      <p className="text-xs text-gray-400">{chapter.summary}</p>
    </div>
  )
}
