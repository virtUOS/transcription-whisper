import { useEffect, useState, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import type { TranscriptionListItem } from '../../api/types'

export function TranscriptionList() {
  const { t } = useTranslation()
  const history = useStore((s) => s.transcriptionHistory)
  const setHistory = useStore((s) => s.setTranscriptionHistory)
  const setTranscriptionId = useStore((s) => s.setTranscriptionId)
  const setTranscriptionStatus = useStore((s) => s.setTranscriptionStatus)
  const setResult = useStore((s) => s.setTranscriptionResult)
  const setSpeakerMappings = useStore((s) => s.setSpeakerMappings)
  const setSummary = useStore((s) => s.setSummary)
  const setProtocol = useStore((s) => s.setProtocol)
  const setFile = useStore((s) => s.setFile)
  const setRefinedUtterances = useStore((s) => s.setRefinedUtterances)
  const setRefinementMetadata = useStore((s) => s.setRefinementMetadata)
  const clearRefinement = useStore((s) => s.clearRefinement)

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const savingRef = useRef(false)
  const clickTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    api.listTranscriptions().then(setHistory).catch(console.error)
  }, [setHistory])

  useEffect(() => {
    if (editingId && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [editingId])

  const reset = useStore((s) => s.reset)

  const doSelect = async (item: TranscriptionListItem) => {
    setTranscriptionId(item.id)
    setTranscriptionStatus(item.status)
    const ext = item.original_filename.split('.').pop()?.toLowerCase() || ''
    setFile({ id: item.file_id, original_filename: item.original_filename, media_type: ext, file_size: item.file_size })
    if (item.status === 'completed') {
      try {
        const result = await api.getTranscription(item.id)
        setResult(result)
        setSpeakerMappings(result.speaker_mappings || {})
        setSummary(result.summary || null)
        setProtocol(result.protocol || null)
        try {
          const refinement = await api.getRefinement(item.id)
          setRefinedUtterances(refinement.utterances)
          setRefinementMetadata(refinement.metadata)
        } catch {
          clearRefinement()
        }
      } catch {
        reset()
        setHistory(history.filter((h) => h.id !== item.id))
      }
    }
  }

  const handleClick = useCallback((item: TranscriptionListItem) => {
    if (clickTimerRef.current) clearTimeout(clickTimerRef.current)
    clickTimerRef.current = setTimeout(() => {
      clickTimerRef.current = null
      doSelect(item)
    }, 250)
  }, [])

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    try {
      await api.deleteTranscription(id)
      setHistory(history.filter((item) => item.id !== id))
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  const handleRenameStart = useCallback((e: React.MouseEvent, item: TranscriptionListItem) => {
    e.stopPropagation()
    if (clickTimerRef.current) {
      clearTimeout(clickTimerRef.current)
      clickTimerRef.current = null
    }
    const baseName = item.original_filename.replace(/\.[^.]+$/, '')
    setEditingId(item.id)
    setEditValue(baseName)
  }, [])

  const handleRenameSave = useCallback(async (item: TranscriptionListItem) => {
    if (savingRef.current) return
    if (editingId !== item.id) return

    const trimmed = editValue.trim()
    setEditingId(null)

    if (!trimmed) return

    const ext = item.original_filename.includes('.')
      ? '.' + item.original_filename.split('.').pop()
      : ''
    const oldFilename = item.original_filename
    const newFilename = trimmed + ext

    if (newFilename === oldFilename) return

    // Optimistic update using current store state to avoid stale closure
    const currentHistory = useStore.getState().transcriptionHistory
    setHistory(currentHistory.map((h) =>
      h.id === item.id ? { ...h, original_filename: newFilename } : h
    ))
    const currentFile = useStore.getState().file
    if (currentFile && currentFile.id === item.file_id) {
      setFile({ ...currentFile, original_filename: newFilename })
    }

    savingRef.current = true
    try {
      await api.renameFile(item.file_id, trimmed)
    } catch {
      // Revert on failure using current store state to avoid stale closure
      const currentHistory = useStore.getState().transcriptionHistory
      setHistory(currentHistory.map((h) =>
        h.id === item.id ? { ...h, original_filename: oldFilename } : h
      ))
      const currentFile = useStore.getState().file
      if (currentFile && currentFile.id === item.file_id) {
        setFile({ ...currentFile, original_filename: oldFilename })
      }
    } finally {
      savingRef.current = false
    }
  }, [editValue, editingId, setHistory, setFile])

  const handleRenameKeyDown = useCallback((e: React.KeyboardEvent, item: TranscriptionListItem) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleRenameSave(item)
    } else if (e.key === 'Escape') {
      setEditingId(null)
    }
  }, [handleRenameSave])

  if (history.length === 0) return null

  return (
    <div className="mx-6 my-4">
      <h2 className="text-sm font-medium text-gray-400 mb-2">{t('transcription.history')}</h2>
      <div className="space-y-1">
        {history.map((item) => (
          <div
            key={item.id}
            onClick={() => handleClick(item)}
            className="w-full flex items-center gap-3 px-3 py-2 bg-gray-800 rounded hover:bg-gray-700 text-sm text-left cursor-pointer"
          >
            {editingId === item.id ? (
              <span className="flex-1 flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                <input
                  ref={inputRef}
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onBlur={() => handleRenameSave(item)}
                  onKeyDown={(e) => handleRenameKeyDown(e, item)}
                  className="bg-gray-700 text-gray-200 px-1 py-0 rounded text-sm flex-1 min-w-0 outline-none focus:ring-1 focus:ring-blue-500"
                />
                <span className="text-gray-500 text-xs">{item.original_filename.includes('.') ? '.' + item.original_filename.split('.').pop() : ''}</span>
              </span>
            ) : (
              <span
                className="text-gray-300 flex-1 truncate"
                onDoubleClick={(e) => handleRenameStart(e, item)}
                title={t('transcription.doubleClickToRename')}
              >
                {item.original_filename}
              </span>
            )}
            <span className="text-gray-500 text-xs">{item.model}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${
              item.status === 'completed' ? 'bg-green-900 text-green-300' :
              item.status === 'failed' ? 'bg-red-900 text-red-300' :
              'bg-yellow-900 text-yellow-300'
            }`}>
              {item.status}
            </span>
            <span className="text-gray-500 text-xs">
              {new Date(item.created_at).toLocaleDateString()}
            </span>
            <button
              onClick={(e) => handleDelete(e, item.id)}
              className="text-gray-500 hover:text-red-400 text-xs px-1"
              title={t('transcription.delete')}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
