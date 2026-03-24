import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { SubtitleRow } from './SubtitleRow'
import { LANGUAGES } from '../../utils/languages'
import type { Utterance } from '../../api/types'

interface SubtitleEditorProps {
  onOpenSpeakerModal?: (speakerId?: string) => void
}

type SearchScope = 'text' | 'speaker' | 'both'

type DisplayEntry =
  | { type: 'utterance'; originalIndex: number; utterance: Utterance; isMatch: boolean }
  | { type: 'separator'; hiddenCount: number }

export function SubtitleEditor({ onOpenSpeakerModal }: SubtitleEditorProps) {
  const { t } = useTranslation()
  const result = useStore((s) => s.transcriptionResult)
  const transcriptionId = useStore((s) => s.transcriptionId)
  const currentTime = useStore((s) => s.currentTime)
  const speakerMappings = useStore((s) => s.speakerMappings)
  const setResult = useStore((s) => s.setTranscriptionResult)
  const dirty = useStore((s) => s.unsavedEdits)
  const setDirty = useStore((s) => s.setUnsavedEdits)
  const refinedUtterances = useStore((s) => s.refinedUtterances)
  const refinementMetadata = useStore((s) => s.refinementMetadata)
  const activeView = useStore((s) => s.activeView)
  const setRefinedUtterances = useStore((s) => s.setRefinedUtterances)
  const setRefinementMetadata = useStore((s) => s.setRefinementMetadata)
  const setActiveView = useStore((s) => s.setActiveView)
  const clearRefinement = useStore((s) => s.clearRefinement)
  const translatedUtterances = useStore((s) => s.translatedUtterances)
  const translationLanguage = useStore((s) => s.translationLanguage)
  const setTranslatedUtterances = useStore((s) => s.setTranslatedUtterances)
  const setTranslationLanguage = useStore((s) => s.setTranslationLanguage)
  const clearTranslation = useStore((s) => s.clearTranslation)
  const config = useStore((s) => s.config)
  const llmAvailable = config?.llm_available ?? false
  const activeRef = useRef<HTMLTableRowElement | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [saving, setSaving] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [searchScope, setSearchScope] = useState<SearchScope>('both')
  const [showRefineModal, setShowRefineModal] = useState(false)
  const [refineContext, setRefineContext] = useState('')
  const [refining, setRefining] = useState(false)
  const [showTranslateModal, setShowTranslateModal] = useState(false)
  const [translateLanguage, setTranslateLanguage] = useState('en')
  const [translating, setTranslating] = useState(false)
  const [summaryCollapsed, setSummaryCollapsed] = useState(false)
  const [editingCell, setEditingCell] = useState<{ index: number; field: string } | null>(null)
  const setSeekTo = useStore((s) => s.setSeekTo)

  const utterances = activeView === 'translated' && translatedUtterances
    ? translatedUtterances
    : activeView === 'refined' && refinedUtterances
      ? refinedUtterances
      : (result?.utterances || [])

  const speakerColorMap = useMemo(() => {
    const speakers = new Set<string>()
    ;(result?.utterances || []).forEach((u) => { if (u.speaker) speakers.add(u.speaker) })
    const sorted = Array.from(speakers).sort()
    const map: Record<string, number> = {}
    sorted.forEach((s, i) => { map[s] = i })
    return map
  }, [result])

  const activeIndex = utterances.findIndex(
    (u) => currentTime >= u.start && currentTime < u.end
  )

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 200)
    return () => clearTimeout(timer)
  }, [searchQuery])

  const displayList = useMemo<DisplayEntry[]>(() => {
    if (!debouncedQuery.trim()) return utterances.map((u, i) => ({ type: 'utterance' as const, originalIndex: i, utterance: u, isMatch: false }))

    const query = debouncedQuery.trim().toLowerCase()

    // Find matching indices
    const matchIndices = new Set<number>()
    utterances.forEach((u, i) => {
      const speakerName = u.speaker ? (speakerMappings[u.speaker] || u.speaker) : ''
      const textMatch = (searchScope === 'text' || searchScope === 'both') && u.text.toLowerCase().includes(query)
      const speakerMatch = (searchScope === 'speaker' || searchScope === 'both') && u.speaker !== null && speakerName.toLowerCase().includes(query)
      if (textMatch || speakerMatch) matchIndices.add(i)
    })

    if (matchIndices.size === 0) return []

    // Expand with context (1 before, 1 after)
    const visibleIndices = new Set<number>()
    matchIndices.forEach(i => {
      if (i > 0) visibleIndices.add(i - 1)
      visibleIndices.add(i)
      if (i < utterances.length - 1) visibleIndices.add(i + 1)
    })

    // Build display list with separators
    const sorted = Array.from(visibleIndices).sort((a, b) => a - b)
    const entries: DisplayEntry[] = []

    for (let j = 0; j < sorted.length; j++) {
      const idx = sorted[j]
      // Add separator if there's a gap
      if (j > 0 && sorted[j] - sorted[j - 1] > 1) {
        entries.push({ type: 'separator', hiddenCount: sorted[j] - sorted[j - 1] - 1 })
      }
      entries.push({ type: 'utterance', originalIndex: idx, utterance: utterances[idx], isMatch: matchIndices.has(idx) })
    }

    // Add leading separator if first visible isn't index 0
    if (sorted[0] > 0) {
      entries.unshift({ type: 'separator', hiddenCount: sorted[0] })
    }
    // Add trailing separator if last visible isn't the last utterance
    if (sorted[sorted.length - 1] < utterances.length - 1) {
      entries.push({ type: 'separator', hiddenCount: utterances.length - 1 - sorted[sorted.length - 1] })
    }

    return entries
  }, [utterances, debouncedQuery, searchScope, speakerMappings])

  const matchCount = useMemo(() =>
    displayList.filter(e => e.type === 'utterance' && e.isMatch).length,
    [displayList]
  )

  const toggleScope = (scope: 'text' | 'speaker') => {
    setSearchScope(prev => {
      if (prev === 'both') return scope === 'text' ? 'speaker' : 'text'
      if (prev === scope) return 'both' // toggling the only active one re-activates both
      return scope
    })
  }

  const clearSearch = () => {
    setSearchQuery('')
    setDebouncedQuery('')
  }

  useEffect(() => {
    if (!debouncedQuery && activeRef.current && containerRef.current) {
      activeRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [activeIndex, debouncedQuery])

  const handleStartEditing = useCallback((index: number, field: string = 'text') => {
    if (activeView === 'refined' || activeView === 'translated') return
    setEditingCell({ index, field })
  }, [activeView])

  const handleStopEditing = useCallback(() => {
    setEditingCell(null)
  }, [])

  // Hotkey handler for subtitle editing navigation
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      if (!target.hasAttribute('data-subtitle-textarea') && !target.hasAttribute('data-subtitle-input')) return

      if (e.key === 'Tab') {
        e.preventDefault()
        if (editingCell === null) return

        // Explicitly blur to trigger save
        if (target instanceof HTMLTextAreaElement || target instanceof HTMLInputElement) target.blur()

        const nextIndex = e.shiftKey
          ? Math.max(0, editingCell.index - 1)
          : Math.min(utterances.length - 1, editingCell.index + 1)

        setEditingCell({ index: nextIndex, field: editingCell.field })
        setSeekTo(utterances[nextIndex].start)
      } else if (e.key === 'Escape') {
        e.preventDefault()
        if (target instanceof HTMLTextAreaElement || target instanceof HTMLInputElement) target.blur()
        setEditingCell(null)
      }
    }

    container.addEventListener('keydown', handleKeyDown)
    return () => container.removeEventListener('keydown', handleKeyDown)
  }, [editingCell, utterances, setSeekTo])

  const handleEditSpeaker = useCallback((speakerId: string) => {
    onOpenSpeakerModal?.(speakerId)
  }, [onOpenSpeakerModal])

  const handleUpdate = useCallback((index: number, field: keyof Utterance, value: string | number) => {
    if (!result) return
    const updated = [...result.utterances]
    updated[index] = { ...updated[index], [field]: value }
    setResult({ ...result, utterances: updated })
    setDirty(true)
  }, [result, setResult, setDirty])

  const handleSave = async () => {
    if (!transcriptionId || !result) return
    setSaving(true)
    try {
      await api.saveTranscription(transcriptionId, result.utterances)
      setDirty(false)
    } catch (e) {
      console.error('Save failed:', e)
    } finally {
      setSaving(false)
    }
  }

  const handleRefine = async () => {
    if (!transcriptionId) return
    setRefining(true)
    try {
      const refinementResult = await api.generateRefinement(transcriptionId, refineContext || undefined)
      setRefinedUtterances(refinementResult.utterances)
      setRefinementMetadata(refinementResult.metadata)
      setActiveView('refined')
      setShowRefineModal(false)
      setRefineContext('')
    } catch {
      console.error('Refinement failed')
    } finally {
      setRefining(false)
    }
  }

  const handleDeleteRefinement = async () => {
    if (!transcriptionId || !confirm(t('editor.confirmDeleteRefinement'))) return
    try {
      await api.deleteRefinement(transcriptionId)
      clearRefinement()
    } catch {
      console.error('Failed to delete refinement')
    }
  }

  const handleTranslate = async () => {
    if (!transcriptionId) return
    setTranslating(true)
    try {
      const translationResult = await api.translateTranscription(transcriptionId, translateLanguage)
      setTranslatedUtterances(translationResult.utterances)
      setTranslationLanguage(translationResult.language)
      setActiveView('translated')
      setShowTranslateModal(false)
    } catch {
      console.error('Translation failed')
    } finally {
      setTranslating(false)
    }
  }

  const handleDeleteTranslation = async () => {
    if (!transcriptionId || !confirm(t('editor.confirmDeleteTranslation'))) return
    try {
      await api.deleteTranslation(transcriptionId)
      clearTranslation()
    } catch {
      console.error('Failed to delete translation')
    }
  }

  const baseUtterances = result?.utterances || []

  if (!utterances.length && !baseUtterances.length) return null

  return (
    <div>
      {/* Search bar — pinned above scrollable area */}
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-800 border-b border-gray-700">
        <div className="relative flex-1">
          <svg className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Escape') clearSearch() }}
            placeholder={t('editor.search.placeholder')}
            className="w-full bg-gray-700 text-gray-200 text-xs pl-7 pr-7 py-1.5 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
          {searchQuery && (
            <button
              onClick={clearSearch}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-200"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => toggleScope('text')}
            className={`px-2 py-1 text-xs rounded ${searchScope === 'text' || searchScope === 'both' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400'}`}
          >
            {t('editor.search.scopeText')}
          </button>
          <button
            onClick={() => toggleScope('speaker')}
            className={`px-2 py-1 text-xs rounded ${searchScope === 'speaker' || searchScope === 'both' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400'}`}
          >
            {t('editor.search.scopeSpeaker')}
          </button>
        </div>
        {debouncedQuery && (
          <span className="text-xs text-gray-500 whitespace-nowrap">
            {t('editor.search.matchCount', { count: matchCount, total: utterances.length })}
          </span>
        )}
      </div>

      {/* Refinement / Translation toolbar */}
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-800 border-b border-gray-700">
        {llmAvailable && !refinementMetadata && (
          <button
            onClick={() => setShowRefineModal(true)}
            className="flex items-center gap-1.5 px-3 py-1 text-xs bg-amber-700/40 text-amber-300 border border-amber-700/50 rounded hover:bg-amber-700/60"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {t('editor.refineTranscription')}
          </button>
        )}
        {llmAvailable && !translatedUtterances && (
          <button
            onClick={() => setShowTranslateModal(true)}
            className="flex items-center gap-1.5 px-3 py-1 text-xs bg-indigo-700/40 text-indigo-300 border border-indigo-700/50 rounded hover:bg-indigo-700/60"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
            </svg>
            {t('editor.translate')}
          </button>
        )}
        {(refinementMetadata || translatedUtterances) && (
          <>
            <div className="flex rounded overflow-hidden border border-gray-600">
              <button
                onClick={() => setActiveView('original')}
                className={`px-3 py-1 text-xs ${activeView === 'original' ? 'bg-gray-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-650'}`}
              >
                {t('editor.viewOriginal')}
              </button>
              {refinementMetadata && (
                <button
                  onClick={() => setActiveView('refined')}
                  className={`px-3 py-1 text-xs ${activeView === 'refined' ? 'bg-amber-700/70 text-amber-200' : 'bg-gray-700 text-gray-400 hover:bg-gray-650'}`}
                >
                  {t('editor.viewRefined')}
                </button>
              )}
              {translatedUtterances && (
                <button
                  onClick={() => setActiveView('translated')}
                  className={`px-3 py-1 text-xs ${activeView === 'translated' ? 'bg-indigo-700/70 text-indigo-200' : 'bg-gray-700 text-gray-400 hover:bg-gray-650'}`}
                >
                  {t('editor.translated')}{translationLanguage ? ` (${translationLanguage.toUpperCase()})` : ''}
                </button>
              )}
            </div>
            <div className="ml-auto flex items-center gap-1">
              {translatedUtterances && (
                <button
                  onClick={handleDeleteTranslation}
                  className="px-2 py-1 text-xs text-gray-500 hover:text-red-400 border border-gray-700 rounded hover:border-red-700/50"
                  title={t('editor.deleteTranslation')}
                >
                  {t('editor.deleteTranslation')}
                </button>
              )}
              {refinementMetadata && (
                <button
                  onClick={handleDeleteRefinement}
                  className="px-2 py-1 text-xs text-gray-500 hover:text-red-400 border border-gray-700 rounded hover:border-red-700/50"
                  title={t('editor.deleteRefinement')}
                >
                  {t('editor.deleteRefinement')}
                </button>
              )}
            </div>
          </>
        )}
      </div>

      {/* Changes summary banner */}
      {activeView === 'refined' && refinementMetadata && (
        <div className="px-3 py-2 bg-amber-900/20 border-b border-amber-700/30">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSummaryCollapsed(c => !c)}
              className="flex items-center gap-1.5 text-xs text-amber-400 font-medium"
            >
              <svg
                className={`w-3 h-3 transition-transform ${summaryCollapsed ? '-rotate-90' : ''}`}
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
              {t('editor.changesSummary')}
              <span className="text-amber-600 font-normal">
                ({refinementMetadata.changed_indices.length})
              </span>
            </button>
            {refinementMetadata.llm_provider && refinementMetadata.llm_model && (
              <span className="ml-auto text-xs text-gray-600">
                {refinementMetadata.llm_provider} / {refinementMetadata.llm_model}
              </span>
            )}
          </div>
          {!summaryCollapsed && (
            <div className="mt-1.5 space-y-1">
              <p className="text-xs text-amber-200/70">{refinementMetadata.changes_summary}</p>
              {refinementMetadata.context && (
                <p className="text-xs text-gray-500">
                  <span className="text-gray-600">{t('editor.changesContext')}: </span>
                  {refinementMetadata.context}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Scrollable subtitle table */}
      <div ref={containerRef} className="overflow-auto max-h-[calc(100vh-22rem)]">
        <table className="w-full border-collapse text-sm table-fixed">
          <thead>
            <tr className="bg-gray-800 text-gray-400 text-xs">
              <th className="px-3 py-2 text-left w-10">#</th>
              <th className="px-2 py-2 text-left w-24">{t('editor.start')}</th>
              <th className="px-2 py-2 text-left w-24">{t('editor.end')}</th>
              <th className="px-2 py-2 text-left w-32">{t('editor.speaker')}</th>
              <th className="px-3 py-2 text-left">{t('editor.text')}</th>
            </tr>
          </thead>
          <tbody>
            {debouncedQuery && displayList.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-3 py-8 text-center text-gray-500 text-xs">
                  {t('editor.search.noMatches')}
                </td>
              </tr>
            ) : (
              displayList.map((entry, i) => {
                if (entry.type === 'separator') {
                  return (
                    <tr key={`sep-${i}`}>
                      <td colSpan={5} className="px-3 py-1 text-center text-gray-600 text-xs">
                        · · · {t('editor.search.hiddenSegments', { count: entry.hiddenCount })} · · ·
                      </td>
                    </tr>
                  )
                }
                return (
                  <SubtitleRow
                    key={entry.originalIndex}
                    ref={entry.originalIndex === activeIndex ? activeRef : undefined}
                    index={entry.originalIndex}
                    utterance={entry.utterance}
                    isActive={entry.originalIndex === activeIndex}
                    isContext={!entry.isMatch && !!debouncedQuery}
                    speakerMappings={speakerMappings}
                    onUpdate={handleUpdate}
                    onEditSpeaker={handleEditSpeaker}
                    speakerColorIndex={entry.utterance.speaker ? speakerColorMap[entry.utterance.speaker] : undefined}
                    highlightTerms={debouncedQuery || undefined}
                    highlightScope={searchScope}
                    isChanged={activeView === 'refined' && (refinementMetadata?.changed_indices.includes(entry.originalIndex) ?? false)}
                    originalText={activeView === 'refined' ? result?.utterances[entry.originalIndex]?.text : undefined}
                    readOnly={activeView === 'refined' || activeView === 'translated'}
                    editingField={editingCell?.index === entry.originalIndex ? editingCell.field : undefined}
                    onStartEditing={handleStartEditing}
                    onStopEditing={handleStopEditing}
                  />
                )
              })
            )}
          </tbody>
        </table>
        <div className="flex items-center gap-2 px-3 py-2 bg-gray-800 text-xs">
          <span className="text-gray-500">{t('editor.editHint')}</span>
          {dirty && (
            <button
              onClick={handleSave}
              disabled={saving}
              className="ml-auto px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-500 disabled:opacity-50"
            >
              {saving ? t('common.loading') : t('editor.saveChanges')}
            </button>
          )}
        </div>
        <details className="px-3 py-1.5 bg-gray-800 border-t border-gray-700 text-xs">
          <summary className="text-gray-500 cursor-pointer hover:text-gray-400 select-none">
            {t('editor.hotkeyLegend')}
          </summary>
          <div className="mt-1.5 mb-1 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-gray-400">
            <kbd className="px-1.5 py-0.5 bg-gray-700 rounded text-gray-300 font-mono text-[10px]">Tab</kbd>
            <span>{t('editor.hotkeyTab')}</span>
            <kbd className="px-1.5 py-0.5 bg-gray-700 rounded text-gray-300 font-mono text-[10px]">Shift+Tab</kbd>
            <span>{t('editor.hotkeyShiftTab')}</span>
            <kbd className="px-1.5 py-0.5 bg-gray-700 rounded text-gray-300 font-mono text-[10px]">Esc</kbd>
            <span>{t('editor.hotkeyEscape')}</span>
          </div>
        </details>
      </div>

      {/* Refine modal */}
      {showRefineModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-xl w-full max-w-md mx-4 p-5">
            <h3 className="text-sm font-medium text-gray-200 mb-3">{t('editor.refineTranscription')}</h3>
            <label className="block text-xs text-gray-400 mb-1">{t('editor.refinementContext')}</label>
            <textarea
              value={refineContext}
              onChange={(e) => setRefineContext(e.target.value)}
              placeholder={t('editor.refinementContextPlaceholder')}
              disabled={refining}
              rows={3}
              className="w-full bg-gray-700 text-gray-200 text-xs px-3 py-2 rounded border border-gray-600 focus:border-amber-500 focus:outline-none resize-none disabled:opacity-50"
            />
            {baseUtterances.length > 50 && (
              <p className="text-xs text-amber-400/80 mt-2">
                {t('editor.refinementWarningLong', { count: baseUtterances.length })}
              </p>
            )}
            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => { setShowRefineModal(false); setRefineContext('') }}
                disabled={refining}
                className="px-3 py-1.5 text-xs text-gray-400 border border-gray-600 rounded hover:border-gray-500 hover:text-gray-200 disabled:opacity-50"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleRefine}
                disabled={refining}
                className="px-3 py-1.5 text-xs bg-amber-700/60 text-amber-200 border border-amber-700/50 rounded hover:bg-amber-700/80 disabled:opacity-50 flex items-center gap-1.5"
              >
                {refining && (
                  <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                )}
                {refining ? t('editor.refining') : t('editor.refine')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Translate modal */}
      {showTranslateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-xl w-full max-w-sm mx-4 p-5">
            <h3 className="text-sm font-medium text-gray-200 mb-3">{t('editor.translateTo')}</h3>
            <label className="block text-xs text-gray-400 mb-1">{t('editor.translationLanguage')}</label>
            <select
              value={translateLanguage}
              onChange={(e) => setTranslateLanguage(e.target.value)}
              disabled={translating}
              className="w-full bg-gray-700 text-gray-200 text-xs px-3 py-2 rounded border border-gray-600 focus:border-indigo-500 focus:outline-none disabled:opacity-50"
            >
              {LANGUAGES.map((lang) => (
                <option key={lang} value={lang}>
                  {t(`languages.${lang}`)}
                </option>
              ))}
            </select>
            {baseUtterances.length > 50 && (
              <p className="text-xs text-indigo-400/80 mt-2">
                {t('editor.translationWarningLong', { count: baseUtterances.length })}
              </p>
            )}
            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => setShowTranslateModal(false)}
                disabled={translating}
                className="px-3 py-1.5 text-xs text-gray-400 border border-gray-600 rounded hover:border-gray-500 hover:text-gray-200 disabled:opacity-50"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleTranslate}
                disabled={translating}
                className="px-3 py-1.5 text-xs bg-indigo-700/60 text-indigo-200 border border-indigo-700/50 rounded hover:bg-indigo-700/80 disabled:opacity-50 flex items-center gap-1.5"
              >
                {translating && (
                  <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                )}
                {translating ? t('editor.translating') : t('editor.translate')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
