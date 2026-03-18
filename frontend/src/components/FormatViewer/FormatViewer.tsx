import { useEffect, useState } from 'react'
import Editor from 'react-simple-code-editor'
import Prism from 'prismjs'
import 'prismjs/components/prism-json'
import 'prismjs/themes/prism-tomorrow.css'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { useTranslation } from 'react-i18next'

interface Props {
  format: string
}

export function FormatViewer({ format }: Props) {
  const { t } = useTranslation()
  const transcriptionId = useStore((s) => s.transcriptionId)
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
    a.download = `transcription.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  const highlight = (code: string) => {
    if (format === 'json') {
      return Prism.highlight(code, Prism.languages.json, 'json')
    }
    return code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }

  if (loading) return <div className="p-4 text-gray-500 text-sm">{t('common.loading')}</div>

  return (
    <div>
      <div className="overflow-auto max-h-96 bg-gray-900 rounded">
        <Editor
          value={content}
          onValueChange={setContent}
          highlight={highlight}
          padding={16}
          style={{
            fontFamily: '"Fira Code", "Fira Mono", monospace',
            fontSize: 12,
            color: '#e2e8f0',
            minHeight: '200px',
          }}
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
