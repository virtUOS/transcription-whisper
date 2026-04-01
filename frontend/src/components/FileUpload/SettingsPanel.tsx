import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { LanguageSelect } from '../LanguageSelect'

export function SettingsPanel() {
  const { t } = useTranslation()
  const config = useStore((s) => s.config)
  const file = useStore((s) => s.file)
  const setTranscriptionId = useStore((s) => s.setTranscriptionId)
  const setTranscriptionStatus = useStore((s) => s.setTranscriptionStatus)

  const [language, setLanguage] = useState<string>('auto')
  const [model, setModel] = useState(config?.default_model || 'base')
  const [detectSpeakers, setDetectSpeakers] = useState(true)
  const [minSpeakers, setMinSpeakers] = useState(1)
  const [maxSpeakers, setMaxSpeakers] = useState(2)
  const [initialPrompt, setInitialPrompt] = useState('')
  const [hotwords, setHotwords] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleTranscribe = async () => {
    if (!file) return
    setSubmitting(true)
    setError(null)
    try {
      const result = await api.startTranscription({
        file_id: file.id,
        language: language === 'auto' ? null : language,
        model,
        min_speakers: detectSpeakers ? minSpeakers : 0,
        max_speakers: detectSpeakers ? maxSpeakers : 0,
        initial_prompt: initialPrompt || null,
        hotwords: hotwords || null,
      })
      setTranscriptionId(result.id)
      setTranscriptionStatus(result.status)
    } catch (e) {
      console.error('Transcription failed:', e)
      setError(e instanceof Error ? e.message : 'Transcription failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="px-6 py-3 bg-gray-800 border-b border-gray-700 space-y-3">
      <div className="flex flex-wrap gap-4 items-end">
        <div className="min-w-0">
          <label className="block text-xs text-gray-400 mb-1">{t('settings.language')}</label>
          <LanguageSelect value={language} onChange={setLanguage} includeAuto className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5" />
        </div>
        <div className="min-w-0">
          <label className="block text-xs text-gray-400 mb-1">{t('settings.model')}</label>
          <select value={model} onChange={(e) => setModel(e.target.value)} className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5">
            {(config?.whisper_models || []).map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2 py-1.5 min-w-0">
          <input type="checkbox" checked={detectSpeakers} onChange={(e) => setDetectSpeakers(e.target.checked)} className="rounded shrink-0" />
          <label className="text-sm text-gray-300">{t('settings.detectSpeakers')}</label>
        </div>
        {detectSpeakers && (
          <>
            <div className="min-w-0">
              <label className="block text-xs text-gray-400 mb-1">{t('settings.minSpeakers')}</label>
              <input type="number" min={1} max={20} value={minSpeakers} onChange={(e) => {
                const val = Math.max(1, Math.min(20, Number(e.target.value)))
                setMinSpeakers(val)
                if (val > maxSpeakers) setMaxSpeakers(val)
              }} className="bg-gray-700 text-white text-sm rounded px-3 py-1.5 w-16" />
            </div>
            <div className="min-w-0">
              <label className="block text-xs text-gray-400 mb-1">{t('settings.maxSpeakers')}</label>
              <input type="number" min={1} max={20} value={maxSpeakers} onChange={(e) => {
                const val = Math.max(1, Math.min(20, Number(e.target.value)))
                setMaxSpeakers(val)
                if (val < minSpeakers) setMinSpeakers(val)
              }} className="bg-gray-700 text-white text-sm rounded px-3 py-1.5 w-16" />
            </div>
          </>
        )}
        <button onClick={() => setShowAdvanced(!showAdvanced)} className="text-sm text-blue-400 hover:text-blue-300 shrink-0">
          {t('settings.advancedOptions')} {showAdvanced ? '▲' : '▼'}
        </button>
        <button onClick={handleTranscribe} disabled={!file || submitting} className="ml-auto px-4 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-500 disabled:opacity-50 shrink-0">
          {submitting ? t('common.loading') : t('transcription.transcribe')}
        </button>
      </div>
      {error && (
        <div className="p-4 bg-red-900/30 rounded-lg border border-red-700">
          <div className="flex items-center gap-3">
            <span className="text-red-400 text-lg">!</span>
            <span className="text-red-300 text-sm">{error}</span>
          </div>
        </div>
      )}
      {showAdvanced && (
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-gray-400 mb-1">{t('settings.initialPrompt')}</label>
            <textarea value={initialPrompt} onChange={(e) => setInitialPrompt(e.target.value)} placeholder={t('settings.initialPromptHelp')} className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 h-16 resize-none" />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-gray-400 mb-1">{t('settings.hotwords')}</label>
            <input value={hotwords} onChange={(e) => setHotwords(e.target.value)} placeholder={t('settings.hotwordsHelp')} className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5" />
          </div>
        </div>
      )}
    </div>
  )
}
