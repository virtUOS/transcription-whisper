import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'

export function TranscriptionList() {
  const { t } = useTranslation()
  const history = useStore((s) => s.transcriptionHistory)
  const setHistory = useStore((s) => s.setTranscriptionHistory)
  const setTranscriptionId = useStore((s) => s.setTranscriptionId)
  const setTranscriptionStatus = useStore((s) => s.setTranscriptionStatus)
  const setResult = useStore((s) => s.setTranscriptionResult)
  const setFile = useStore((s) => s.setFile)

  useEffect(() => {
    api.listTranscriptions().then(setHistory).catch(console.error)
  }, [setHistory])

  const handleSelect = async (item: typeof history[0]) => {
    setTranscriptionId(item.id)
    setTranscriptionStatus(item.status)
    const ext = item.original_filename.split('.').pop()?.toLowerCase() || ''
    setFile({ id: item.file_id, original_filename: item.original_filename, media_type: ext, file_size: 0 })
    if (item.status === 'completed') {
      const result = await api.getTranscription(item.id)
      setResult(result)
    }
  }

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    try {
      await api.deleteTranscription(id)
      setHistory(history.filter((item) => item.id !== id))
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  if (history.length === 0) return null

  return (
    <div className="mx-6 my-4">
      <h2 className="text-sm font-medium text-gray-400 mb-2">{t('transcription.history')}</h2>
      <div className="space-y-1">
        {history.map((item) => (
          <div
            key={item.id}
            onClick={() => handleSelect(item)}
            className="w-full flex items-center gap-3 px-3 py-2 bg-gray-800 rounded hover:bg-gray-700 text-sm text-left cursor-pointer"
          >
            <span className="text-gray-300 flex-1 truncate">{item.original_filename}</span>
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
