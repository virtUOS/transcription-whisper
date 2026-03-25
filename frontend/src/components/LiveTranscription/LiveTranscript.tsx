import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import type { LiveTranscriptionLine } from '../../api/types'

const SPEAKER_COLORS = [
  'text-blue-400', 'text-green-400', 'text-purple-400', 'text-orange-400',
  'text-pink-400', 'text-cyan-400', 'text-yellow-400', 'text-red-400',
]

function speakerColor(speaker: string | null): string {
  if (!speaker) return 'text-gray-400'
  const num = parseInt(speaker.replace(/\D/g, ''), 10)
  return SPEAKER_COLORS[(num - 1) % SPEAKER_COLORS.length] || 'text-gray-400'
}

function formatMs(ms: number): string {
  const totalSec = Math.floor(ms / 1000)
  const m = Math.floor(totalSec / 60)
  const s = totalSec % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

interface Props {
  lines: LiveTranscriptionLine[]
  bufferText: string
}

export default function LiveTranscript({ lines, bufferText }: Props) {
  const { t } = useTranslation()
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [lines, bufferText])

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto rounded-lg bg-gray-900 p-4 font-mono text-sm"
    >
      {lines.length === 0 && !bufferText && (
        <p className="text-gray-500 italic">{t('live.waitingForSpeech')}</p>
      )}
      {lines.map((line, i) => (
        <div key={i} className="mb-2 flex gap-2">
          <span className="shrink-0 text-gray-600 text-xs mt-0.5 w-12 text-right">
            {formatMs(line.start)}
          </span>
          {line.speaker && (
            <span className={`shrink-0 font-semibold ${speakerColor(line.speaker)}`}>
              {line.speaker}:
            </span>
          )}
          <span className="text-gray-200">{line.text}</span>
        </div>
      ))}
      {bufferText && (
        <div className="mb-2 flex gap-2">
          <span className="shrink-0 w-12" />
          <span className="text-gray-500 italic">{bufferText}</span>
        </div>
      )}
    </div>
  )
}
