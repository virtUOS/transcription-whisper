import { useState, useMemo, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'

const SPEAKER_PLACEHOLDER_RE = /^SPEAKER_\d+$/

interface Props {
  isOpen: boolean
  onClose: () => void
  focusSpeaker?: string
}

export function SpeakerMapping({ isOpen, onClose, focusSpeaker }: Props) {
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

  // Sync local mappings when store mappings change (e.g. on reopen)
  useEffect(() => {
    if (isOpen) setLocalMappings(speakerMappings)
  }, [isOpen, speakerMappings])

  // Collect custom (non-placeholder) names for datalist suggestions
  const customNames = useMemo(() => {
    const names = new Set<string>()
    Object.values(localMappings).forEach((name) => {
      if (name && !SPEAKER_PLACEHOLDER_RE.test(name)) names.add(name)
    })
    return Array.from(names).sort()
  }, [localMappings])

  // Auto-focus the input for the focused speaker
  const inputRefs = useRef<Record<string, HTMLInputElement | null>>({})
  useEffect(() => {
    if (isOpen && focusSpeaker && inputRefs.current[focusSpeaker]) {
      // Small delay to let the modal render
      requestAnimationFrame(() => {
        inputRefs.current[focusSpeaker!]?.focus()
        inputRefs.current[focusSpeaker!]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      })
    }
  }, [isOpen, focusSpeaker])

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
          {speakers.map((speaker) => {
            const mappedName = localMappings[speaker] || ''
            const isAutoName = !mappedName || SPEAKER_PLACEHOLDER_RE.test(mappedName)
            return (
              <div key={speaker} className="flex items-center gap-3">
                <span className={`text-sm w-24 shrink-0 ${isAutoName ? 'text-gray-500 italic' : 'text-gray-200 font-medium'}`}>
                  {mappedName || speaker}
                </span>
                <span className="text-gray-500">{'\u2192'}</span>
                <input
                  ref={(el) => { inputRefs.current[speaker] = el }}
                  value={localMappings[speaker] || ''}
                  onChange={(e) => setLocalMappings({ ...localMappings, [speaker]: e.target.value })}
                  placeholder={speaker}
                  list="speaker-name-suggestions"
                  className="flex-1 bg-gray-700 text-white text-sm rounded px-3 py-1.5"
                />
              </div>
            )
          })}
        </div>
        <datalist id="speaker-name-suggestions">
          {customNames.map((name) => (
            <option key={name} value={name} />
          ))}
        </datalist>
        {speakers.length === 0 && (
          <p className="text-gray-500 text-sm">{t('editor.noSpeakers')}</p>
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
