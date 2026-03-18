import { useCallback, useEffect, useRef } from 'react'
import { useStore } from '../../store'
import { SubtitleRow } from './SubtitleRow'
import type { Utterance } from '../../api/types'

export function SubtitleEditor() {
  const result = useStore((s) => s.transcriptionResult)
  const currentTime = useStore((s) => s.currentTime)
  const speakerMappings = useStore((s) => s.speakerMappings)
  const setResult = useStore((s) => s.setTranscriptionResult)
  const activeRef = useRef<HTMLTableRowElement | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)

  const utterances = result?.utterances || []

  const activeIndex = utterances.findIndex(
    (u) => currentTime >= u.start && currentTime < u.end
  )

  useEffect(() => {
    if (activeRef.current && containerRef.current) {
      activeRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [activeIndex])

  const handleUpdate = useCallback((index: number, field: keyof Utterance, value: string | number) => {
    if (!result) return
    const updated = [...result.utterances]
    updated[index] = { ...updated[index], [field]: value }
    setResult({ ...result, utterances: updated })
  }, [result, setResult])

  if (!utterances.length) return null

  return (
    <div ref={containerRef} className="overflow-auto max-h-96">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-gray-800 text-gray-400 text-xs">
            <th className="px-3 py-2 text-left w-10">#</th>
            <th className="px-2 py-2 text-left w-24">Start</th>
            <th className="px-2 py-2 text-left w-24">End</th>
            <th className="px-2 py-2 text-left w-32">Speaker</th>
            <th className="px-3 py-2 text-left">Text</th>
          </tr>
        </thead>
        <tbody>
          {utterances.map((utt, i) => (
            <SubtitleRow
              key={i}
              ref={i === activeIndex ? activeRef : undefined}
              index={i}
              utterance={utt}
              isActive={i === activeIndex}
              speakerMappings={speakerMappings}
              onUpdate={handleUpdate}
            />
          ))}
        </tbody>
      </table>
      <div className="flex gap-2 px-3 py-2 bg-gray-800 text-xs">
        <span className="text-gray-500">Double-click cells to edit. Click timestamps to seek.</span>
      </div>
    </div>
  )
}
