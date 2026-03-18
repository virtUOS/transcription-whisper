import { useEffect, useState } from 'react'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { useTranslation } from 'react-i18next'

interface Props {
  format: string
}

export function FormatViewer({ format }: Props) {
  const { t } = useTranslation()
  const transcriptionId = useStore((s) => s.transcriptionId)
  const file = useStore((s) => s.file)
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!transcriptionId) return
    setLoading(true)
    api.exportTranscription(transcriptionId, format)
      .then(setContent)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [transcriptionId, format])

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

  if (loading) return <div className="p-4 text-gray-500 text-sm">{t('common.loading')}</div>

  return (
    <div>
      <div className="overflow-auto max-h-96 bg-gray-900 rounded border border-gray-700">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          spellCheck={false}
          className="w-full min-h-[200px] p-4 bg-transparent text-gray-300 text-xs font-mono resize-y focus:outline-none"
          style={{ tabSize: 2 }}
        />
      </div>
      <div className="flex justify-end mt-2">
        <button onClick={handleDownload} className="px-4 py-1.5 bg-green-700 text-white text-sm rounded hover:bg-green-600">
          {t('editor.download')} {format.toUpperCase()}
        </button>
      </div>
    </div>
  )
}
