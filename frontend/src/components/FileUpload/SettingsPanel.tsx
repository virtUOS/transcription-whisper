import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { LanguageSelect } from '../LanguageSelect'
import { PresetSelect } from '../PresetSelect/PresetSelect'

export interface SettingsPanelValues {
  language: string
  model: string
  detectSpeakers: boolean
  minSpeakers: number
  maxSpeakers: number
  initialPrompt: string
  hotwords: string
  selectedPresetId: string | null
  showAdvanced: boolean
}

interface SettingsPanelProps {
  values: SettingsPanelValues
  onChange: (patch: Partial<SettingsPanelValues>) => void
  saveError?: string | null
}

export function SettingsPanel({ values, onChange, saveError = null }: SettingsPanelProps) {
  const { t } = useTranslation()
  const config = useStore((s) => s.config)
  const transcriptionPresets = useStore((s) => s.transcriptionPresets)
  const setTranscriptionPresets = useStore((s) => s.setTranscriptionPresets)
  const bundles = useStore((s) => s.bundles)
  const activeBundleId = useStore((s) => s.activeBundleId)
  const setActiveBundleId = useStore((s) => s.setActiveBundleId)

  const handleLoadPreset = (presetId: string | null) => {
    onChange({ selectedPresetId: presetId })
    if (!presetId) return
    const preset = transcriptionPresets.find((p) => p.id === presetId)
    if (!preset) return
    onChange({
      language: preset.language || 'auto',
      model: preset.model,
      detectSpeakers: preset.min_speakers > 0 || preset.max_speakers > 0,
      minSpeakers: preset.min_speakers || 1,
      maxSpeakers: preset.max_speakers || 2,
      initialPrompt: preset.initial_prompt || '',
      hotwords: preset.hotwords || '',
    })
  }

  const handleSavePreset = async (name: string) => {
    const preset = await api.createTranscriptionPreset({
      name,
      language: values.language === 'auto' ? null : values.language,
      model: values.model,
      min_speakers: values.detectSpeakers ? values.minSpeakers : 0,
      max_speakers: values.detectSpeakers ? values.maxSpeakers : 0,
      initial_prompt: values.initialPrompt || null,
      hotwords: values.hotwords || null,
    })
    setTranscriptionPresets([...transcriptionPresets, preset])
    onChange({ selectedPresetId: preset.id })
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

  const groupClass = 'flex flex-wrap items-end gap-3 border border-gray-700 rounded-md px-3 pt-1 pb-3'
  const legendClass = 'text-[10px] uppercase tracking-wider text-gray-500 px-1'

  return (
    <div className="px-6 py-3 bg-gray-800 border-b border-gray-700 space-y-3">
      {/* Container row — semantic groups laid out side-by-side, wrap freely */}
      <div className="flex flex-wrap gap-3 items-stretch">
        {/* Presets group */}
        <fieldset className={groupClass}>
          <legend className={legendClass}>{t('settings.groups.presets')}</legend>
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
          {transcriptionPresets.length > 0 && (
            <div className="min-w-0">
              <label className="block text-xs text-gray-400 mb-1">{t('presets.transcription')}</label>
              <select
                value={values.selectedPresetId || ''}
                onChange={(e) => handleLoadPreset(e.target.value || null)}
                className="bg-gray-700 text-white text-sm rounded px-3 py-1.5 min-w-[140px]"
              >
                <option value="">{t('presets.selectPreset')}</option>
                {transcriptionPresets.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
          )}
          <div className="self-end">
            <PresetSelect
              presets={[]}
              selectedId={null}
              onSelect={() => {}}
              onSave={handleSavePreset}
              hideDropdown
            />
          </div>
        </fieldset>

        {/* Transcription group (Language + Quality) */}
        <fieldset className={groupClass}>
          <legend className={legendClass}>{t('settings.groups.transcription')}</legend>
          <div className="min-w-0">
            <label htmlFor="upload-language-field" className="block text-xs text-gray-400 mb-1">{t('settings.language')}</label>
            <LanguageSelect
              id="upload-language-field"
              value={values.language}
              onChange={(v) => onChange({ language: v })}
              includeAuto
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5"
            />
          </div>
          <div className="min-w-0">
            <label htmlFor="upload-model-field" className="block text-xs text-gray-400 mb-1">{t('settings.model')}</label>
            {(() => {
              const models = config?.whisper_models || []
              if (models.length === 1) {
                const m = models[0]
                const label = t(`settings.modelLabels.${m}`, '')
                return (
                  <output id="upload-model-field" className="block w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5">
                    {label ? `${label} (${m})` : m}
                  </output>
                )
              }
              return (
                <select
                  id="upload-model-field"
                  value={values.model}
                  onChange={(e) => onChange({ model: e.target.value })}
                  className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5"
                >
                  {models.map((m) => {
                    const label = t(`settings.modelLabels.${m}`, '')
                    return <option key={m} value={m}>{label ? `${label} (${m})` : m}</option>
                  })}
                </select>
              )
            })()}
          </div>
        </fieldset>

        {/* Speakers group (checkbox + optional min/max — never split across wraps) */}
        <fieldset className={groupClass}>
          <legend className={legendClass}>{t('settings.groups.speakers')}</legend>
          <label className="flex items-center gap-2 py-1.5">
            <input
              type="checkbox"
              checked={values.detectSpeakers}
              onChange={(e) => onChange({ detectSpeakers: e.target.checked })}
              className="rounded shrink-0"
            />
            <span className="text-sm text-gray-300">{t('settings.detectSpeakers')}</span>
          </label>
          {values.detectSpeakers && (
            <>
              <div className="min-w-0">
                <label className="block text-xs text-gray-400 mb-1">{t('settings.minSpeakers')}</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={values.minSpeakers}
                  onChange={(e) => {
                    const val = Math.max(1, Math.min(20, Number(e.target.value)))
                    onChange({
                      minSpeakers: val,
                      maxSpeakers: val > values.maxSpeakers ? val : values.maxSpeakers,
                    })
                  }}
                  className="bg-gray-700 text-white text-sm rounded px-3 py-1.5 w-16"
                />
              </div>
              <div className="min-w-0">
                <label className="block text-xs text-gray-400 mb-1">{t('settings.maxSpeakers')}</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={values.maxSpeakers}
                  onChange={(e) => {
                    const val = Math.max(1, Math.min(20, Number(e.target.value)))
                    onChange({
                      maxSpeakers: val,
                      minSpeakers: val < values.minSpeakers ? val : values.minSpeakers,
                    })
                  }}
                  className="bg-gray-700 text-white text-sm rounded px-3 py-1.5 w-16"
                />
              </div>
            </>
          )}
        </fieldset>

        <button
          onClick={() => onChange({ showAdvanced: !values.showAdvanced })}
          className="ml-auto self-end text-sm text-blue-400 hover:text-blue-300 py-1.5 shrink-0"
        >
          {t('settings.advancedOptions')} {values.showAdvanced ? '▲' : '▼'}
        </button>
      </div>

      {saveError && (
        <div className="p-4 bg-red-900/30 rounded-lg border border-red-700">
          <div className="flex items-center gap-3">
            <span className="text-red-400 text-lg" aria-hidden="true">!</span>
            <span className="text-red-300 text-sm">{saveError}</span>
          </div>
        </div>
      )}

      {/* Advanced options panel — wrapped in a labeled container to match other groups */}
      {values.showAdvanced && (
        <fieldset className={`${groupClass} w-full`}>
          <legend className={legendClass}>{t('settings.advancedOptions')}</legend>
          <div className="flex flex-wrap gap-3 w-full">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-xs text-gray-400 mb-1">{t('settings.initialPrompt')}</label>
              <textarea
                value={values.initialPrompt}
                onChange={(e) => onChange({ initialPrompt: e.target.value })}
                placeholder={t('settings.initialPromptHelp')}
                className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 h-16 resize-none"
              />
            </div>
            <div className="flex-1 min-w-[200px]">
              <label className="block text-xs text-gray-400 mb-1">{t('settings.hotwords')}</label>
              <input
                value={values.hotwords}
                onChange={(e) => onChange({ hotwords: e.target.value })}
                placeholder={t('settings.hotwordsHelp')}
                className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5"
              />
            </div>
          </div>
        </fieldset>
      )}
    </div>
  )
}
