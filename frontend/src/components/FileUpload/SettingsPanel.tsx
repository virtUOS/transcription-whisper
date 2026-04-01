import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { LanguageSelect } from '../LanguageSelect'
import { PresetSelect } from '../PresetSelect/PresetSelect'

export function SettingsPanel() {
  const { t } = useTranslation()
  const config = useStore((s) => s.config)
  const file = useStore((s) => s.file)
  const uploading = useStore((s) => s.uploading)
  const setTranscriptionId = useStore((s) => s.setTranscriptionId)
  const setTranscriptionStatus = useStore((s) => s.setTranscriptionStatus)
  const transcriptionPresets = useStore((s) => s.transcriptionPresets)
  const setTranscriptionPresets = useStore((s) => s.setTranscriptionPresets)
  const bundles = useStore((s) => s.bundles)
  const activeBundleId = useStore((s) => s.activeBundleId)
  const setActiveBundleId = useStore((s) => s.setActiveBundleId)

  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null)
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
  const [pendingTranscription, setPendingTranscription] = useState(false)

  const handleLoadPreset = (presetId: string | null) => {
    setSelectedPresetId(presetId)
    if (!presetId) return
    const preset = transcriptionPresets.find((p) => p.id === presetId)
    if (!preset) return
    setLanguage(preset.language || 'auto')
    setModel(preset.model)
    setDetectSpeakers(preset.min_speakers > 0 || preset.max_speakers > 0)
    setMinSpeakers(preset.min_speakers || 1)
    setMaxSpeakers(preset.max_speakers || 2)
    setInitialPrompt(preset.initial_prompt || '')
    setHotwords(preset.hotwords || '')
  }

  const handleSavePreset = async (name: string) => {
    const preset = await api.createTranscriptionPreset({
      name,
      language: language === 'auto' ? null : language,
      model,
      min_speakers: detectSpeakers ? minSpeakers : 0,
      max_speakers: detectSpeakers ? maxSpeakers : 0,
      initial_prompt: initialPrompt || null,
      hotwords: hotwords || null,
    })
    setTranscriptionPresets([...transcriptionPresets, preset])
    setSelectedPresetId(preset.id)
  }

  const handleLoadBundle = (bundleId: string | null) => {
    setActiveBundleId(bundleId)
    if (!bundleId) return
    const bundle = bundles.find((b) => b.id === bundleId)
    if (!bundle) return
    if (bundle.transcription_preset_id) {
      handleLoadPreset(bundle.transcription_preset_id)
    }
  }

  const handleTranscribe = useCallback(async () => {
    if (!file && uploading) {
      setPendingTranscription(true)
      return
    }
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
  }, [file, uploading, language, model, detectSpeakers, minSpeakers, maxSpeakers, initialPrompt, hotwords, setTranscriptionId, setTranscriptionStatus])

  useEffect(() => {
    if (pendingTranscription && file) {
      setPendingTranscription(false)
      handleTranscribe()
    }
  }, [file, pendingTranscription, handleTranscribe])

  useEffect(() => {
    if (pendingTranscription && !uploading && !file) {
      setPendingTranscription(false)
    }
  }, [uploading, file, pendingTranscription])

  return (
    <div className="px-6 py-3 bg-gray-800 border-b border-gray-700 space-y-3">
      {(transcriptionPresets.length > 0 || bundles.length > 0) && (
        <div className="flex flex-wrap gap-4 items-center mb-2">
          {bundles.length > 0 && (
            <div className="min-w-0">
              <label className="block text-xs text-gray-400 mb-1">{t('presets.bundles')}</label>
              <select
                value={activeBundleId || ''}
                onChange={(e) => handleLoadBundle(e.target.value || null)}
                className="bg-gray-700 text-white text-sm rounded px-3 py-1.5"
              >
                <option value="">{t('presets.selectBundle')}</option>
                {bundles.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}{b.is_default ? ` (${t('presets.bundle.isDefault')})` : ''}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="min-w-0">
            <label className="block text-xs text-gray-400 mb-1">{t('presets.transcription')}</label>
            <PresetSelect
              presets={transcriptionPresets}
              selectedId={selectedPresetId}
              onSelect={handleLoadPreset}
              onSave={handleSavePreset}
            />
          </div>
        </div>
      )}
      {transcriptionPresets.length === 0 && bundles.length === 0 && (
        <div className="flex justify-end mb-1">
          <PresetSelect
            presets={[]}
            selectedId={null}
            onSelect={() => {}}
            onSave={handleSavePreset}
          />
        </div>
      )}
      <div className="flex flex-wrap gap-4 items-end">
        <div className="min-w-0">
          <label className="block text-xs text-gray-400 mb-1">{t('settings.language')}</label>
          <LanguageSelect value={language} onChange={setLanguage} includeAuto className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5" />
        </div>
        <div className="min-w-0">
          <label className="block text-xs text-gray-400 mb-1">{t('settings.model')}</label>
          <select value={model} onChange={(e) => setModel(e.target.value)} className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5">
            {(config?.whisper_models || []).map((m) => {
              const label = t(`settings.modelLabels.${m}`, '')
              return <option key={m} value={m}>{label ? `${label} (${m})` : m}</option>
            })}
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
        <button
          onClick={handleTranscribe}
          disabled={(!file && !uploading) || submitting}
          className={`ml-auto px-4 py-1.5 text-white text-sm rounded disabled:opacity-50 shrink-0 ${
            pendingTranscription ? 'bg-amber-600 hover:bg-amber-500' : 'bg-blue-600 hover:bg-blue-500'
          }`}
        >
          {submitting
            ? t('common.loading')
            : pendingTranscription
              ? t('transcription.transcribeWhenReady')
              : uploading && !file
                ? t('transcription.transcribeWhenReady')
                : t('transcription.transcribe')}
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
