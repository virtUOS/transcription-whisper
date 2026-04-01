import { useMemo } from 'react'
import { useStore } from '../../store'
import { useTranslation } from 'react-i18next'
import type { Utterance } from '../../api/types'

interface Props {
  format: string
}

function pad(n: number, digits = 2) {
  return n.toString().padStart(digits, '0')
}

function formatSrtTime(ms: number): string {
  const totalSec = Math.floor(ms / 1000)
  const h = Math.floor(totalSec / 3600)
  const m = Math.floor((totalSec % 3600) / 60)
  const s = totalSec % 60
  const millis = ms % 1000
  return `${pad(h)}:${pad(m)}:${pad(s)},${pad(millis, 3)}`
}

function formatVttTime(ms: number): string {
  return formatSrtTime(ms).replace(',', '.')
}

function getSpeakerLabel(utt: Utterance, mappings: Record<string, string>): string {
  if (!utt.speaker) return ''
  return mappings[utt.speaker] || utt.speaker
}

function generateSrt(utterances: Utterance[], mappings: Record<string, string>): string {
  return utterances.map((utt, i) => {
    const speaker = getSpeakerLabel(utt, mappings)
    const prefix = speaker ? `[${speaker}]: ` : ''
    return `${i + 1}\n${formatSrtTime(utt.start)} --> ${formatSrtTime(utt.end)}\n${prefix}${utt.text}`
  }).join('\n\n')
}

function generateVtt(utterances: Utterance[], mappings: Record<string, string>): string {
  const cues = utterances.map((utt) => {
    const speaker = getSpeakerLabel(utt, mappings)
    const prefix = speaker ? `[${speaker}]: ` : ''
    return `${formatVttTime(utt.start)} --> ${formatVttTime(utt.end)}\n${prefix}${utt.text}`
  }).join('\n\n')
  return `WEBVTT\n\n${cues}`
}

function generateTxt(utterances: Utterance[], mappings: Record<string, string>): string {
  return utterances.map((utt) => {
    const speaker = getSpeakerLabel(utt, mappings)
    return speaker ? `${speaker}: ${utt.text}` : utt.text
  }).join('\n')
}

function generateJson(utterances: Utterance[], mappings: Record<string, string>): string {
  const mapped = utterances.map((utt) => ({
    start: utt.start,
    end: utt.end,
    text: utt.text,
    speaker: getSpeakerLabel(utt, mappings) || utt.speaker,
  }))
  return JSON.stringify(mapped, null, 2)
}

export function FormatViewer({ format }: Props) {
  const { t } = useTranslation()
  const result = useStore((s) => s.transcriptionResult)
  const speakerMappings = useStore((s) => s.speakerMappings)
  const file = useStore((s) => s.file)
  const refinedUtterances = useStore((s) => s.refinedUtterances)
  const translatedUtterances = useStore((s) => s.translatedUtterances)
  const activeView = useStore((s) => s.activeView)

  const content = useMemo(() => {
    const originalUtterances = result?.utterances || []
    const utterances = activeView === 'translated' && translatedUtterances
      ? translatedUtterances
      : activeView === 'refined' && refinedUtterances
        ? refinedUtterances
        : originalUtterances

    switch (format) {
      case 'srt': return generateSrt(utterances, speakerMappings)
      case 'vtt': return generateVtt(utterances, speakerMappings)
      case 'txt': return generateTxt(utterances, speakerMappings)
      case 'json': {
        if (activeView === 'refined' && refinedUtterances) {
          return JSON.stringify({
            utterances: originalUtterances.map(u => ({ ...u, speaker: getSpeakerLabel(u, speakerMappings) || u.speaker })),
            refined_utterances: refinedUtterances.map(u => ({ ...u, speaker: getSpeakerLabel(u, speakerMappings) || u.speaker })),
          }, null, 2)
        }
        return generateJson(utterances, speakerMappings)
      }
      default: return ''
    }
  }, [result, refinedUtterances, translatedUtterances, activeView, speakerMappings, format])

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const baseName = file?.original_filename?.replace(/\.[^.]+$/, '') || 'transcription'
    a.download = `${baseName}.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadBtn = (
    <button onClick={handleDownload} className="px-4 py-1.5 bg-green-700 text-white text-sm rounded hover:bg-green-600">
      {t('editor.download')} {format.toUpperCase()}
    </button>
  )

  return (
    <div>
      <div className="flex justify-end mb-2">
        {downloadBtn}
      </div>
      <div className="overflow-auto max-h-96 bg-gray-900 rounded border border-gray-700">
        <textarea
          value={content}
          readOnly
          spellCheck={false}
          className="w-full min-h-[200px] p-4 bg-transparent text-gray-300 text-xs font-mono resize-y focus:outline-none"
          style={{ tabSize: 2 }}
        />
      </div>
      <div className="flex justify-end mt-2">
        {downloadBtn}
      </div>
    </div>
  )
}
