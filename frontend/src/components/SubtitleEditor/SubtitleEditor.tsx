import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { SubtitleRow } from './SubtitleRow'
import type { Utterance } from '../../api/types'

export function SubtitleEditor() {
  const { t } = useTranslation()
  const result = useStore((s) => s.transcriptionResult)
  const transcriptionId = useStore((s) => s.transcriptionId)
  const currentTime = useStore((s) => s.currentTime)
  const speakerMappings = useStore((s) => s.speakerMappings)
  const setResult = useStore((s) => s.setTranscriptionResult)
  const dirty = useStore((s) => s.unsavedEdits)
  const setDirty = useStore((s) => s.setUnsavedEdits)
  const activeRef = useRef<HTMLTableRowElement | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [saving, setSaving] = useState(false)

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
    setDirty(true)
  }, [result, setResult, setDirty])

  const handleSave = async () => {
    if (!transcriptionId || !result) return
    setSaving(true)
    try {
      await api.saveTranscription(transcriptionId, result.utterances)
      setDirty(false)
    } catch (e) {
      console.error('Save failed:', e)
    } finally {
      setSaving(false)
    }
  }

  if (!utterances.length) return null

  return (
    <div ref={containerRef} className="overflow-auto max-h-96">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-gray-800 text-gray-400 text-xs">
            <th className="px-3 py-2 text-left w-10">#</th>
            <th className="px-2 py-2 text-left w-24">{t('editor.start')}</th>
            <th className="px-2 py-2 text-left w-24">{t('editor.end')}</th>
            <th className="px-2 py-2 text-left w-32">{t('editor.speaker')}</th>
            <th className="px-3 py-2 text-left">{t('editor.text')}</th>
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
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-800 text-xs">
        <span className="text-gray-500">{t('editor.editHint')}</span>
        {dirty && (
          <button
            onClick={handleSave}
            disabled={saving}
            className="ml-auto px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-500 disabled:opacity-50"
          >
            {saving ? t('common.loading') : t('editor.saveChanges')}
          </button>
        )}
      </div>
    </div>
  )
}
