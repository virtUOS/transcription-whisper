import { useState, forwardRef } from 'react'
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import type { Utterance } from '../../api/types'

function formatTimestamp(ms: number): string {
  const s = Math.floor(ms / 1000)
  const m = Math.floor(s / 60)
  const h = Math.floor(m / 60)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${pad(h)}:${pad(m % 60)}:${pad(s % 60)}`
}

function highlightText(text: string, query: string): ReactNode {
  if (!query) return text
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escaped})`, 'gi')
  const parts = text.split(regex)
  if (parts.length === 1) return text
  const queryLower = query.toLowerCase()
  return parts.map((part, i) =>
    part.toLowerCase() === queryLower
      ? <span key={i} className="bg-yellow-600/40 text-yellow-200 rounded px-0.5">{part}</span>
      : part
  )
}

interface Props {
  index: number
  utterance: Utterance
  isActive: boolean
  isContext?: boolean
  speakerMappings: Record<string, string>
  onUpdate: (index: number, field: keyof Utterance, value: string | number) => void
  highlightTerms?: string
  highlightScope?: 'text' | 'speaker' | 'both'
  isChanged?: boolean
  originalText?: string
  readOnly?: boolean
}

export const SubtitleRow = forwardRef<HTMLTableRowElement, Props>(function SubtitleRow({ index, utterance, isActive, isContext, speakerMappings, onUpdate, highlightTerms, highlightScope, isChanged, originalText, readOnly }, ref) {
  const { t } = useTranslation()
  const setSeekTo = useStore((s) => s.setSeekTo)
  const [editingField, setEditingField] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [showDiff, setShowDiff] = useState(false)

  const speakerDisplay = utterance.speaker
    ? speakerMappings[utterance.speaker] || utterance.speaker
    : ''

  const startEdit = (field: string, value: string) => {
    if (readOnly) return
    setEditingField(field)
    setEditValue(value)
  }

  const commitEdit = (field: keyof Utterance) => {
    if (field === 'start' || field === 'end') {
      const parts = editValue.split(':').map(Number)
      const ms = ((parts[0] || 0) * 3600 + (parts[1] || 0) * 60 + (parts[2] || 0)) * 1000
      onUpdate(index, field, ms)
    } else {
      onUpdate(index, field, editValue)
    }
    setEditingField(null)
  }

  const renderCell = (field: keyof Utterance, value: string, displayContent?: ReactNode, className?: string) => {
    if (editingField === field) {
      return (
        <input
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onBlur={() => commitEdit(field)}
          onKeyDown={(e) => e.key === 'Enter' && commitEdit(field)}
          className="bg-gray-600 text-white text-xs px-1 py-0.5 rounded w-full"
          autoFocus
        />
      )
    }
    return (
      <span
        className={`cursor-pointer hover:text-blue-400 ${className || ''}`}
        onDoubleClick={() => startEdit(field, value)}
      >
        {displayContent ?? value}
      </span>
    )
  }

  const handleRowClick = () => {
    if (isChanged) setShowDiff(d => !d)
  }

  return (
    <>
      <tr
        ref={ref}
        onClick={handleRowClick}
        className={`border-b border-gray-700 text-xs ${isActive ? 'bg-blue-900/30' : 'hover:bg-gray-800'} ${isContext ? 'opacity-50' : ''} ${isChanged ? 'border-l-2 border-l-amber-500' : ''} ${isChanged ? 'cursor-pointer' : ''}`}
      >
        <td className="px-3 py-2 text-gray-500">
          {index + 1}
          {isChanged && (
            <span className="ml-1 inline-block w-1.5 h-1.5 rounded-full bg-amber-500 align-middle" title={t('editor.utteranceChanged')} />
          )}
        </td>
        <td className="px-2 py-2 text-blue-400 cursor-pointer" onClick={(e) => { e.stopPropagation(); setSeekTo(utterance.start) }}>
          {renderCell('start', formatTimestamp(utterance.start))}
        </td>
        <td className="px-2 py-2 text-blue-400 cursor-pointer" onClick={(e) => { e.stopPropagation(); setSeekTo(utterance.end) }}>
          {renderCell('end', formatTimestamp(utterance.end))}
        </td>
        <td className="px-2 py-2 text-green-400">
          {renderCell('speaker', speakerDisplay,
            highlightTerms && (highlightScope === 'speaker' || highlightScope === 'both')
              ? highlightText(speakerDisplay, highlightTerms)
              : undefined
          )}
        </td>
        <td className="px-3 py-2 text-gray-200">
          {renderCell('text', utterance.text,
            highlightTerms && (highlightScope === 'text' || highlightScope === 'both')
              ? highlightText(utterance.text, highlightTerms)
              : undefined
          )}
        </td>
      </tr>
      {showDiff && originalText && (
        <tr className="bg-gray-800/50">
          <td colSpan={5} className="px-3 py-2">
            <div className="flex gap-4 text-xs">
              <div className="flex-1">
                <span className="text-gray-500 font-medium">{t('editor.originalText')}:</span>
                <p className="text-red-400/70 mt-0.5">{originalText}</p>
              </div>
              <div className="flex-1">
                <span className="text-gray-500 font-medium">{t('editor.refinedText')}:</span>
                <p className="text-green-400/70 mt-0.5">{utterance.text}</p>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
})
