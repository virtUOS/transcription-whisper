import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { ChapterCard } from '../SummaryView/ChapterCard'
import { ProtocolCard } from '../ProtocolView/ProtocolCard'
import { formatTime, downloadText } from '../../utils/format'
import { LANGUAGES } from '../../utils/languages'
import type { AnalysisTemplate, ChapterHint, SummaryChapter } from '../../api/types'

// Type guards for smart result detection
interface SummaryShape {
  summary: string
  chapters: SummaryChapter[]
  llm_provider?: string | null
  llm_model?: string | null
}

interface ProtocolShape {
  title: string
  participants: string[]
  key_points: Array<{ topic: string; speaker: string; timestamp: number | null; content: string }>
  decisions: Array<{ decision: string; timestamp: number | null }>
  action_items: Array<{ task: string; assignee: string; timestamp: number | null }>
  llm_provider?: string | null
  llm_model?: string | null
}

function isSummaryShape(result: unknown): result is SummaryShape {
  if (!result || typeof result !== 'object') return false
  const r = result as Record<string, unknown>
  return typeof r.summary === 'string' && Array.isArray(r.chapters)
}

function isProtocolShape(result: unknown): result is ProtocolShape {
  if (!result || typeof result !== 'object') return false
  const r = result as Record<string, unknown>
  return typeof r.title === 'string' && Array.isArray(r.key_points) && Array.isArray(r.decisions) && Array.isArray(r.action_items)
}

function resultToText(result: unknown, t: (key: string) => string): string {
  if (isSummaryShape(result)) {
    let text = result.summary + '\n'
    if (result.chapters.length > 0) {
      text += '\n'
      result.chapters.forEach((ch, i) => {
        text += `${i + 1}. ${ch.title} [${formatTime(ch.start_time)} — ${formatTime(ch.end_time)}]\n${ch.summary}\n\n`
      })
    }
    return text.trimEnd()
  }
  if (isProtocolShape(result)) {
    let text = `${t('editor.protocol')}: ${result.title}\n`
    text += `${t('editor.participants')}: ${result.participants.join(', ')}\n`
    if (result.key_points.length > 0) {
      text += `\n${t('editor.keyPoints').toUpperCase()}\n`
      result.key_points.forEach((kp, i) => {
        const ts = kp.timestamp !== null ? `[${formatTime(kp.timestamp)}] ` : ''
        text += `${i + 1}. ${ts}${kp.speaker} — ${kp.topic}\n   ${kp.content}\n\n`
      })
    }
    if (result.decisions.length > 0) {
      text += `${t('editor.decisions').toUpperCase()}\n`
      result.decisions.forEach((d, i) => {
        const ts = d.timestamp !== null ? `[${formatTime(d.timestamp)}] ` : ''
        text += `${i + 1}. ${ts}${d.decision}\n\n`
      })
    }
    if (result.action_items.length > 0) {
      text += `${t('editor.actionItems').toUpperCase()}\n`
      result.action_items.forEach((ai, i) => {
        const ts = ai.timestamp !== null ? ` (${formatTime(ai.timestamp)})` : ''
        text += `${i + 1}. ${ai.assignee} — ${ai.task}${ts}\n\n`
      })
    }
    return text.trimEnd()
  }
  if (typeof result === 'string') return result
  return JSON.stringify(result, null, 2)
}

export function AnalysisView() {
  const { t } = useTranslation()
  const transcriptionId = useStore((s) => s.transcriptionId)
  const analysisResult = useStore((s) => s.analysisResult)
  const setAnalysisResult = useStore((s) => s.setAnalysisResult)
  const analysisPrompt = useStore((s) => s.analysisPrompt)
  const setAnalysisPrompt = useStore((s) => s.setAnalysisPrompt)
  const analysisTemplate = useStore((s) => s.analysisTemplate)
  const setAnalysisTemplate = useStore((s) => s.setAnalysisTemplate)
  const file = useStore((s) => s.file)
  const detectedLanguage = useStore((s) => s.transcriptionResult?.language)

  const [templates, setTemplates] = useState<AnalysisTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const [customPrompt, setCustomPrompt] = useState('')
  const [promptExpanded, setPromptExpanded] = useState(false)
  const [language, setLanguage] = useState<string>(detectedLanguage || 'en')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)

  // Chapter hints (for summary template)
  const [hintsExpanded, setHintsExpanded] = useState(false)
  const [hints, setHints] = useState<ChapterHint[]>([])

  // Agenda (for agenda template)
  const [agenda, setAgenda] = useState('')

  const baseName = file?.original_filename?.replace(/\.[^.]+$/, '') || 'transcription'

  // Fetch templates on mount
  useEffect(() => {
    api.getAnalysisTemplates().then((tpls) => {
      setTemplates(tpls)
      if (tpls.length > 0 && !selectedTemplate) {
        setSelectedTemplate(tpls[0].id)
        setCustomPrompt(tpls[0].default_prompt)
      }
    }).catch(console.error)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const currentTemplate = templates.find((tp) => tp.id === selectedTemplate)

  const handleSelectTemplate = useCallback((id: string | null) => {
    setSelectedTemplate(id)
    if (id === null) {
      setCustomPrompt('')
    } else {
      const tpl = templates.find((tp) => tp.id === id)
      if (tpl) setCustomPrompt(tpl.default_prompt)
    }
  }, [templates])

  const handleResetPrompt = useCallback(() => {
    if (selectedTemplate) {
      const tpl = templates.find((tp) => tp.id === selectedTemplate)
      if (tpl) setCustomPrompt(tpl.default_prompt)
    } else {
      setCustomPrompt('')
    }
  }, [selectedTemplate, templates])

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
      const validHints = hints.filter(h => h.title?.trim() || h.description?.trim())
        .map(h => ({
          ...(h.title?.trim() ? { title: h.title.trim() } : {}),
          ...(h.description?.trim() ? { description: h.description.trim() } : {}),
        }))

      const isCustom = selectedTemplate === null
      const promptChanged = currentTemplate && customPrompt !== currentTemplate.default_prompt

      const result = await api.generateAnalysis(transcriptionId, {
        template: isCustom ? null : selectedTemplate,
        custom_prompt: isCustom || promptChanged ? customPrompt : null,
        language,
        chapter_hints: selectedTemplate === 'summary' && validHints.length > 0 ? validHints : null,
        agenda: selectedTemplate === 'agenda' && agenda.trim() ? agenda.trim() : null,
      })
      setAnalysisResult(result)
      setAnalysisPrompt(customPrompt)
      setAnalysisTemplate(selectedTemplate)
    } catch (e) {
      setError(e instanceof Error ? e.message : t('analysis.generationFailed'))
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!transcriptionId || !confirm(t('analysis.confirmDelete'))) return
    try {
      await api.deleteAnalysis(transcriptionId)
      setAnalysisResult(null)
      setAnalysisPrompt(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    }
  }

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

  // Resolve display label for the analysis type
  const resolvedTemplate = (() => {
    const r = analysisResult as Record<string, unknown> | null
    return r?.template as string | null ?? analysisTemplate
  })()
  const translateTemplateName = (id: string) =>
    t(`analysis.template${id.charAt(0).toUpperCase()}${id.slice(1)}`,
      templates.find((tp) => tp.id === id)?.name ?? id)

  const templateLabel = resolvedTemplate
    ? translateTemplateName(resolvedTemplate)
    : t('analysis.customPrompt')

  // Loading state
  if (loading) {
    const generatingLabel = selectedTemplate
      ? translateTemplateName(selectedTemplate)
      : t('analysis.customPrompt')

    return (
      <div className="p-6 text-center text-gray-400">
        <div className="animate-spin h-6 w-6 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
        {t('analysis.generatingType', { type: generatingLabel })}
      </div>
    )
  }

  // Result display
  if (analysisResult) {
    const fullText = resultToText(analysisResult, t)

    return (
      <div className="p-4 space-y-4">
        {/* Analysis type badge */}
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 text-xs font-medium rounded-full bg-purple-900/40 text-purple-300 border border-purple-700/50">
            {templateLabel}
          </span>
        </div>

        {/* Smart result rendering */}
        {isSummaryShape(analysisResult) && (
          <>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <p className="text-sm text-gray-300 whitespace-pre-wrap">{analysisResult.summary}</p>
            </div>
            {analysisResult.chapters.length > 0 && (
              <div>
                <h2 className="text-sm font-medium text-gray-400 mb-2">{t('editor.chapters')}</h2>
                <div className="space-y-2">
                  {analysisResult.chapters.map((ch, i) => (
                    <ChapterCard key={i} chapter={ch} index={i} />
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {isProtocolShape(analysisResult) && (
          <>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h2 className="text-base font-medium text-white mb-1">{analysisResult.title}</h2>
              <p className="text-xs text-gray-400">
                {t('editor.participants')}: {analysisResult.participants.join(', ')}
              </p>
            </div>
            {analysisResult.key_points.length > 0 && (
              <div>
                <h2 className="text-sm font-medium text-gray-400 mb-2">{t('editor.keyPoints')}</h2>
                <div className="space-y-2">
                  {analysisResult.key_points.map((kp, i) => (
                    <ProtocolCard key={i} timestamp={kp.timestamp} label={`${kp.speaker} — ${kp.topic}`} description={kp.content} />
                  ))}
                </div>
              </div>
            )}
            {analysisResult.decisions.length > 0 && (
              <div>
                <h2 className="text-sm font-medium text-gray-400 mb-2">{t('editor.decisions')}</h2>
                <div className="space-y-2">
                  {analysisResult.decisions.map((d, i) => (
                    <ProtocolCard key={i} timestamp={d.timestamp} label={d.decision} description="" />
                  ))}
                </div>
              </div>
            )}
            {analysisResult.action_items.length > 0 && (
              <div>
                <h2 className="text-sm font-medium text-gray-400 mb-2">{t('editor.actionItems')}</h2>
                <div className="space-y-2">
                  {analysisResult.action_items.map((ai, i) => (
                    <ProtocolCard key={i} timestamp={ai.timestamp} label={ai.assignee} description={ai.task} />
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {!isSummaryShape(analysisResult) && !isProtocolShape(analysisResult) && (
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">{fullText}</pre>
          </div>
        )}

        {/* Prompt used (collapsible) */}
        {analysisPrompt && (
          <details className="border border-gray-700 rounded-lg">
            <summary className="px-4 py-2.5 text-sm text-gray-400 cursor-pointer hover:bg-gray-800 rounded-lg">
              {t('analysis.promptUsed')}
            </summary>
            <div className="px-4 pb-4">
              <pre className="text-xs text-gray-500 whitespace-pre-wrap font-mono">{analysisPrompt}</pre>
            </div>
          </details>
        )}

        {/* Copy / Download / Delete */}
        <div className="flex justify-end gap-2 pt-3 border-t border-gray-700">
          <button onClick={handleDelete} className="px-4 py-1.5 text-sm rounded flex items-center gap-2 text-red-300 bg-red-900/40 hover:bg-red-800/60 mr-auto">
            {t('analysis.delete')}
          </button>
          <button onClick={() => handleCopy(fullText, 'all')} className={btnCopy}>
            {copied === 'all' ? checkIcon : copyIcon}
            {copied === 'all' ? t('editor.copied') : t('analysis.copyResult')}
          </button>
          <button onClick={() => downloadText(fullText, `${baseName}_analysis.txt`)} className={btnDownload}>
            {downloadIcon}
            {t('analysis.downloadResult')}
          </button>
        </div>

        {/* Model info */}
        {(() => {
          const r = analysisResult as Record<string, unknown>
          if (r?.llm_provider && r?.llm_model) {
            return (
              <p className="text-xs text-gray-500 text-right">
                {t('editor.generatedWithModel', { provider: r.llm_provider, model: r.llm_model })}
              </p>
            )
          }
          return null
        })()}
      </div>
    )
  }

  // Configuration / generation form
  return (
    <div className="p-6 space-y-4">
      {/* Template selector */}
      <div>
        <label className="block text-xs text-gray-400 mb-2">{t('analysis.selectTemplate')}</label>
        <div className="flex flex-wrap gap-2">
          {templates.map((tpl) => (
            <button
              key={tpl.id}
              onClick={() => handleSelectTemplate(tpl.id)}
              className={`px-4 py-2 text-sm rounded-lg border transition-colors ${
                selectedTemplate === tpl.id
                  ? 'border-purple-500 bg-purple-900/40 text-purple-300'
                  : 'border-gray-700 bg-gray-800 text-gray-300 hover:border-gray-500'
              }`}
              title={tpl.description}
            >
              {translateTemplateName(tpl.id)}
            </button>
          ))}
          <button
            onClick={() => handleSelectTemplate(null)}
            className={`px-4 py-2 text-sm rounded-lg border transition-colors ${
              selectedTemplate === null
                ? 'border-purple-500 bg-purple-900/40 text-purple-300'
                : 'border-gray-700 bg-gray-800 text-gray-300 hover:border-gray-500'
            }`}
          >
            {t('analysis.customPrompt')}
          </button>
        </div>
      </div>

      {/* Chapter hints — only for summary template */}
      {selectedTemplate === 'summary' && (
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
      )}

      {/* Agenda textarea — only for agenda template */}
      {selectedTemplate === 'agenda' && (
        <div>
          <label className="block text-xs text-gray-400 mb-1">{t('analysis.agenda')}</label>
          <textarea
            value={agenda}
            onChange={(e) => setAgenda(e.target.value)}
            placeholder={t('analysis.agendaPlaceholder')}
            rows={5}
            className="w-full px-3 py-2 text-sm bg-gray-800 border border-gray-600 rounded-lg text-gray-200 placeholder-gray-500 resize-y"
          />
        </div>
      )}

      {/* Prompt editor (collapsible) */}
      <div className="border border-gray-700 rounded-lg">
        <button
          onClick={() => setPromptExpanded(!promptExpanded)}
          className="w-full px-4 py-2.5 text-sm text-left text-gray-300 hover:bg-gray-800 rounded-lg flex items-center justify-between"
        >
          {t('analysis.customizePrompt')}
          <svg
            className={`w-4 h-4 transition-transform ${promptExpanded ? 'rotate-180' : ''}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {promptExpanded && (
          <div className="px-4 pb-4 space-y-2">
            <textarea
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              rows={8}
              className="w-full px-3 py-2 text-sm bg-gray-800 border border-gray-600 rounded-lg text-gray-200 placeholder-gray-500 resize-y font-mono"
            />
            {selectedTemplate && (
              <button
                onClick={handleResetPrompt}
                className="text-sm text-purple-400 hover:text-purple-300"
              >
                {t('analysis.resetPrompt')}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Language selector + Generate button */}
      <div className="flex items-center justify-center gap-3">
        <div>
          <label className="block text-xs text-gray-400 mb-1">{t('editor.outputLanguage')}</label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
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
          {analysisResult ? t('analysis.regenerate') : t('analysis.generate')}
        </button>
      </div>

      {error && <p className="text-red-400 text-sm mt-2 text-center">{error}</p>}
    </div>
  )
}
