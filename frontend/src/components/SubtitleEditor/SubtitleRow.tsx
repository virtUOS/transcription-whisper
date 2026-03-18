import { useState, forwardRef } from 'react'
import { useStore } from '../../store'
import type { Utterance } from '../../api/types'

function formatTimestamp(ms: number): string {
  const s = Math.floor(ms / 1000)
  const m = Math.floor(s / 60)
  const h = Math.floor(m / 60)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${pad(h)}:${pad(m % 60)}:${pad(s % 60)}`
}

interface Props {
  index: number
  utterance: Utterance
  isActive: boolean
  speakerMappings: Record<string, string>
  onUpdate: (index: number, field: keyof Utterance, value: string | number) => void
}

export const SubtitleRow = forwardRef<HTMLTableRowElement, Props>(function SubtitleRow({ index, utterance, isActive, speakerMappings, onUpdate }, ref) {
  const setSeekTo = useStore((s) => s.setSeekTo)
  const [editingField, setEditingField] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')

  const speakerDisplay = utterance.speaker
    ? speakerMappings[utterance.speaker] || utterance.speaker
    : ''

  const startEdit = (field: string, value: string) => {
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

  const renderCell = (field: keyof Utterance, value: string, className?: string) => {
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
        {value}
      </span>
    )
  }

  return (
    <tr ref={ref} className={`border-b border-gray-700 text-xs ${isActive ? 'bg-blue-900/30' : 'hover:bg-gray-800'}`}>
      <td className="px-3 py-2 text-gray-500">{index + 1}</td>
      <td className="px-2 py-2 text-blue-400 cursor-pointer" onClick={() => setSeekTo(utterance.start)}>
        {renderCell('start', formatTimestamp(utterance.start))}
      </td>
      <td className="px-2 py-2 text-blue-400 cursor-pointer" onClick={() => setSeekTo(utterance.end)}>
        {renderCell('end', formatTimestamp(utterance.end))}
      </td>
      <td className="px-2 py-2 text-green-400">
        {renderCell('speaker', speakerDisplay)}
      </td>
      <td className="px-3 py-2 text-gray-200">
        {renderCell('text', utterance.text)}
      </td>
    </tr>
  )
})
