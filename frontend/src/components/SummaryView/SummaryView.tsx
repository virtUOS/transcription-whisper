import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { ChapterCard } from './ChapterCard'
import { formatTime, downloadText } from '../../utils/format'
import type { SummaryResult, SummaryChapter } from '../../api/types'

function summaryToText(summary: SummaryResult): string {
  let text = summary.summary + '\n'
  if (summary.chapters.length > 0) {
    text += '\n'
    summary.chapters.forEach((ch, i) => {
      text += `${i + 1}. ${ch.title} [${formatTime(ch.start_time)} — ${formatTime(ch.end_time)}]\n${ch.summary}\n\n`
    })
  }
  return text.trimEnd()
}

function chaptersToText(chapters: SummaryChapter[]): string {
  return chapters.map((ch, i) =>
    `${i + 1}. ${ch.title} [${formatTime(ch.start_time)} — ${formatTime(ch.end_time)}]\n${ch.summary}`
  ).join('\n\n')
}

export function SummaryView() {
  const { t } = useTranslation()
  const transcriptionId = useStore((s) => s.transcriptionId)
  const summary = useStore((s) => s.summary)
  const setSummary = useStore((s) => s.setSummary)
  const file = useStore((s) => s.file)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)

  const baseName = file?.original_filename?.replace(/\.[^.]+$/, '') || 'transcription'

  const handleCopy = async (text: string, key: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

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
        {t('editor.generatingSummary')}
      </div>
    )
  }

  if (!summary) return null

  const fullText = summaryToText(summary)

  const copyIcon = (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
  )
  const checkIcon = (
    <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
  )
  const downloadIcon = (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
  )

  const btnCopy = "px-4 py-1.5 text-sm rounded flex items-center gap-2 text-gray-300 bg-gray-700 hover:bg-gray-600"
  const btnDownload = "px-4 py-1.5 text-sm rounded flex items-center gap-2 text-white bg-green-700 hover:bg-green-600"

  return (
    <div className="p-4 space-y-4">
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <p className="text-sm text-gray-300 whitespace-pre-wrap">{summary.summary}</p>
        <div className="flex justify-end gap-2 mt-3">
          <button onClick={() => handleCopy(summary.summary, 'summary')} className={btnCopy}>
            {copied === 'summary' ? checkIcon : copyIcon}
            {copied === 'summary' ? t('editor.copied') : t('editor.copySummary')}
          </button>
          <button onClick={() => downloadText(summary.summary, `${baseName}_summary.txt`)} className={btnDownload}>
            {downloadIcon}
            {t('editor.downloadSummary')}
          </button>
        </div>
      </div>

      {summary.chapters.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-gray-400 mb-2">{t('editor.chapters')}</h2>
          <div className="space-y-2">
            {summary.chapters.map((ch, i) => (
              <ChapterCard key={i} chapter={ch} index={i} />
            ))}
          </div>
          <div className="flex justify-end gap-2 mt-3">
            <button onClick={() => handleCopy(chaptersToText(summary.chapters), 'chapters')} className={btnCopy}>
              {copied === 'chapters' ? checkIcon : copyIcon}
              {copied === 'chapters' ? t('editor.copied') : t('editor.copyChapters')}
            </button>
            <button onClick={() => downloadText(chaptersToText(summary.chapters), `${baseName}_chapters.txt`)} className={btnDownload}>
              {downloadIcon}
              {t('editor.downloadChapters')}
            </button>
          </div>
        </div>
      )}

      <div className="flex justify-end gap-2 pt-3 border-t border-gray-700">
        <button onClick={() => handleCopy(fullText, 'all')} className={btnCopy}>
          {copied === 'all' ? checkIcon : copyIcon}
          {copied === 'all' ? t('editor.copied') : t('editor.copyAll')}
        </button>
        <button onClick={() => downloadText(fullText, `${baseName}_summary.txt`)} className={btnDownload}>
          {downloadIcon}
          {t('editor.downloadAll')}
        </button>
      </div>
    </div>
  )
}
