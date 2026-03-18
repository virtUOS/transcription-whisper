import { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'

interface Props {
  isOpen: boolean
  onClose: () => void
}

export function SpeakerMapping({ isOpen, onClose }: Props) {
  const { t } = useTranslation()
  const result = useStore((s) => s.transcriptionResult)
  const speakerMappings = useStore((s) => s.speakerMappings)
  const setSpeakerMappings = useStore((s) => s.setSpeakerMappings)
  const transcriptionId = useStore((s) => s.transcriptionId)

  const speakers = useMemo(() => {
    if (!result) return []
    const set = new Set<string>()
    result.utterances.forEach((u) => { if (u.speaker) set.add(u.speaker) })
    return Array.from(set).sort()
  }, [result])

  const [localMappings, setLocalMappings] = useState<Record<string, string>>(speakerMappings)

  const handleApply = async () => {
    if (!transcriptionId) return
    await api.updateSpeakers(transcriptionId, localMappings)
    setSpeakerMappings(localMappings)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-96 max-h-[80vh] overflow-auto">
        <h2 className="text-lg font-medium text-white mb-4">{t('editor.speakerNames')}</h2>
        <div className="space-y-3">
          {speakers.map((speaker) => (
            <div key={speaker} className="flex items-center gap-3">
              <span className="text-gray-400 text-sm w-24 shrink-0">{speaker}</span>
              <span className="text-gray-500">{'\u2192'}</span>
              <input
                value={localMappings[speaker] || ''}
                onChange={(e) => setLocalMappings({ ...localMappings, [speaker]: e.target.value })}
                placeholder={speaker}
                className="flex-1 bg-gray-700 text-white text-sm rounded px-3 py-1.5"
              />
            </div>
          ))}
        </div>
        {speakers.length === 0 && (
          <p className="text-gray-500 text-sm">No speakers detected.</p>
        )}
        <div className="flex justify-end gap-3 mt-6">
          <button onClick={onClose} className="px-4 py-1.5 text-sm text-gray-300 hover:text-white">
            {t('common.cancel')}
          </button>
          <button onClick={handleApply} className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-500">
            {t('editor.apply')}
          </button>
        </div>
      </div>
    </div>
  )
}
