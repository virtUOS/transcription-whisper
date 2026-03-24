import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { ChapterCard } from './ChapterCard'
import { formatTime, downloadText } from '../../utils/format'
import { LANGUAGES } from '../../utils/languages'
import type { SummaryResult, SummaryChapter, ChapterHint } from '../../api/types'

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
  const detectedLanguage = useStore((s) => s.transcriptionResult?.language)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)
  const [hintsExpanded, setHintsExpanded] = useState(false)
  const [hints, setHints] = useState<ChapterHint[]>([])
  const [summaryLanguage, setSummaryLanguage] = useState<string>(detectedLanguage || 'en')

  const baseName = file?.original_filename?.replace(/\.[^.]+$/, '') || 'transcription'

  const handleAddHint = useCallback(() => {
    if (hints.length >= 30) return
    setHints(prev => [...prev, { title: '', description: '' }])
  }, [hints.length])

  const handleRemoveHint = useCallback((index: number) => {
    setHints(prev => prev.filter((_, i) => i !== index))
  }, [])

  const handleHintChange = useCallback((index: number, field: 'title' | 'description', value: string) => {
    setHints(prev => prev.map((h, i) => i === index ? { ...h, [field]: value } : h))
  }, [])

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
      // Filter out empty hints (neither title nor description)
      const validHints = hints.filter(h => h.title?.trim() || h.description?.trim())
        .map(h => ({
          ...(h.title?.trim() ? { title: h.title.trim() } : {}),
          ...(h.description?.trim() ? { description: h.description.trim() } : {}),
        }))
      const result = await api.generateSummary(
        transcriptionId,
        validHints.length > 0 ? validHints : undefined,
        summaryLanguage,
      )
      setSummary(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Summary generation failed')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteChapter = useCallback(async (index: number) => {
    if (!summary || !transcriptionId) return
    try {
      const updated = await api.deleteChapter(transcriptionId, index)
      setSummary(updated)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete chapter')
    }
  }, [summary, transcriptionId, setSummary])

  const handleDelete = async () => {
    if (!transcriptionId || !confirm(t('editor.confirmDeleteSummary'))) return
    try {
      // Pre-fill hints from existing summary before deleting
      if (summary?.chapter_hints?.length) {
        setHints(summary.chapter_hints.map(h => ({ title: h.title || '', description: h.description || '' })))
        setHintsExpanded(true)
      }
      await api.deleteSummary(transcriptionId)
      setSummary(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    }
  }

  if (!summary && !loading) {
    return (
      <div className="p-6 space-y-4">
        {/* Collapsible chapter hints section */}
        <div className="border border-gray-700 rounded-lg">
          <button
            onClick={() => setHintsExpanded(!hintsExpanded)}
            className="w-full px-4 py-2.5 text-sm text-left text-gray-300 hover:bg-gray-800 rounded-lg flex items-center justify-between"
          >
            {t('editor.chapterHints')}
            <svg
              className={`w-4 h-4 transition-transform ${hintsExpanded ? 'rotate-180' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {hintsExpanded && (
            <div className="px-4 pb-4 space-y-2">
              {hints.map((hint, i) => (
                <div key={i} className="flex items-start gap-2">
                  <input
                    type="text"
                    value={hint.title || ''}
                    onChange={(e) => handleHintChange(i, 'title', e.target.value)}
                    placeholder={t('editor.chapterTitle')}
                    className="flex-1 px-3 py-1.5 text-sm bg-gray-800 border border-gray-600 rounded text-gray-200 placeholder-gray-500"
                  />
                  <input
                    type="text"
                    value={hint.description || ''}
                    onChange={(e) => handleHintChange(i, 'description', e.target.value)}
                    placeholder={t('editor.chapterDescription')}
                    className="flex-1 px-3 py-1.5 text-sm bg-gray-800 border border-gray-600 rounded text-gray-200 placeholder-gray-500"
                  />
                  <button
                    onClick={() => handleRemoveHint(i)}
                    className="p-1.5 text-gray-400 hover:text-red-400"
                    title={t('editor.removeChapter')}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
              <button
                onClick={handleAddHint}
                disabled={hints.length >= 30}
                className="text-sm text-purple-400 hover:text-purple-300 disabled:text-gray-600 disabled:cursor-not-allowed"
              >
                + {hints.length >= 30 ? t('editor.maxChaptersReached') : t('editor.addChapter')}
              </button>
            </div>
          )}
        </div>

        <div className="flex items-center justify-center gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">{t('editor.summaryLanguage')}</label>
            <select
              value={summaryLanguage}
              onChange={(e) => setSummaryLanguage(e.target.value)}
              className="bg-gray-700 text-white text-sm rounded px-3 py-1.5"
            >
              {LANGUAGES.map((code) => (
                <option key={code} value={code}>{t(`languages.${code}`, code)}</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleGenerate}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-500 self-end"
          >
            {t('editor.summary')} ✨
          </button>
          {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
        </div>
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
              <ChapterCard key={i} chapter={ch} index={i} onDelete={() => handleDeleteChapter(i)} />
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
        <button onClick={handleDelete} className="px-4 py-1.5 text-sm rounded flex items-center gap-2 text-red-300 bg-red-900/40 hover:bg-red-800/60 mr-auto">
          {t('editor.deleteSummary')}
        </button>
        <button onClick={() => handleCopy(fullText, 'all')} className={btnCopy}>
          {copied === 'all' ? checkIcon : copyIcon}
          {copied === 'all' ? t('editor.copied') : t('editor.copyAll')}
        </button>
        <button onClick={() => downloadText(fullText, `${baseName}_summary.txt`)} className={btnDownload}>
          {downloadIcon}
          {t('editor.downloadAll')}
        </button>
      </div>

      {summary.llm_provider && summary.llm_model && (
        <p className="text-xs text-gray-500 text-right">
          {t('editor.generatedWithModel', { provider: summary.llm_provider, model: summary.llm_model })}
        </p>
      )}
    </div>
  )
}
