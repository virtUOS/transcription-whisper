import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { ChapterCard } from './ChapterCard'

export function SummaryView() {
  const { t } = useTranslation()
  const transcriptionId = useStore((s) => s.transcriptionId)
  const summary = useStore((s) => s.summary)
  const setSummary = useStore((s) => s.setSummary)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async () => {
    if (!transcriptionId) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.generateSummary(transcriptionId)
      setSummary(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Summary generation failed')
    } finally {
      setLoading(false)
    }
  }

  if (!summary && !loading) {
    return (
      <div className="p-6 text-center">
        <button
          onClick={handleGenerate}
          className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-500"
        >
          {t('editor.summary')} ✨
        </button>
        {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="p-6 text-center text-gray-400">
        <div className="animate-spin h-6 w-6 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
        Generating summary...
      </div>
    )
  }

  if (!summary) return null

  return (
    <div className="p-4 space-y-4">
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <p className="text-sm text-gray-300 whitespace-pre-wrap">{summary.summary}</p>
      </div>

      {summary.chapters.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-gray-400 mb-2">Chapters</h2>
          <div className="space-y-2">
            {summary.chapters.map((ch, i) => (
              <ChapterCard key={i} chapter={ch} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
