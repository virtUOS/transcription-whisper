import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { SubtitleRow } from './SubtitleRow'
import type { Utterance } from '../../api/types'

type SearchScope = 'text' | 'speaker' | 'both'

type DisplayEntry =
  | { type: 'utterance'; originalIndex: number; utterance: Utterance; isMatch: boolean }
  | { type: 'separator'; hiddenCount: number }

export function SubtitleEditor() {
  const { t } = useTranslation()
  const result = useStore((s) => s.transcriptionResult)
  const transcriptionId = useStore((s) => s.transcriptionId)
  const currentTime = useStore((s) => s.currentTime)
  const speakerMappings = useStore((s) => s.speakerMappings)
  const setResult = useStore((s) => s.setTranscriptionResult)
  const dirty = useStore((s) => s.unsavedEdits)
  const setDirty = useStore((s) => s.setUnsavedEdits)
  const activeRef = useRef<HTMLTableRowElement | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [saving, setSaving] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [searchScope, setSearchScope] = useState<SearchScope>('both')

  const utterances = result?.utterances || []

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

  if (!utterances.length) return null

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

      {/* Scrollable subtitle table */}
      <div ref={containerRef} className="overflow-auto max-h-96">
        <table className="w-full border-collapse text-sm">
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
                    highlightTerms={debouncedQuery || undefined}
                    highlightScope={searchScope}
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
      </div>
    </div>
  )
}
