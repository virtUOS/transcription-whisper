import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { LANGUAGES, filterEnabledLanguages, isLanguageEnabled } from '../../utils/languages'
import type {
  TranscriptionPreset,
  TranscriptionPresetCreate,
  AnalysisPreset,
  AnalysisPresetCreate,
  RefinementPreset,
  RefinementPresetCreate,
  PresetBundle,
  PresetBundleCreate,
} from '../../api/types'

// ---------------------------------------------------------------------------
// TranscriptionPresetsList
// ---------------------------------------------------------------------------

function TranscriptionPresetsList() {
  const { t } = useTranslation()
  const config = useStore((s) => s.config)
  const presets = useStore((s) => s.transcriptionPresets)
  const setPresets = useStore((s) => s.setTranscriptionPresets)

  const emptyForm: TranscriptionPresetCreate = { name: '', language: null, model: '', initial_prompt: null, hotwords: null }
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<TranscriptionPresetCreate>(emptyForm)
  const [saving, setSaving] = useState(false)

  const models = config?.whisper_models ?? []
  const defaultModel = config?.default_model ?? ''
  const enabledLanguages = config?.enabled_languages ?? []

  const openNew = () => {
    setEditingId(null)
    setForm({ ...emptyForm, model: defaultModel })
    setShowForm(true)
  }

  const openEdit = (p: TranscriptionPreset) => {
    setEditingId(p.id)
    const model = models.length === 1 ? models[0] : p.model
    const language = p.language && !isLanguageEnabled(p.language, enabledLanguages) ? null : p.language
    setForm({ name: p.name, language, model, initial_prompt: p.initial_prompt, hotwords: p.hotwords })
    setShowForm(true)
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingId(null)
    setForm(emptyForm)
  }

  const handleSave = async () => {
    if (!form.name.trim()) return
    setSaving(true)
    try {
      if (editingId) {
        const updated = await api.updateTranscriptionPreset(editingId, form)
        setPresets(presets.map((p) => (p.id === editingId ? updated : p)))
      } else {
        const created = await api.createTranscriptionPreset(form)
        setPresets([...presets, created])
      }
      handleCancel()
    } catch (err) {
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm(t('presets.confirmDelete'))) return
    try {
      await api.deleteTranscriptionPreset(id)
      setPresets(presets.filter((p) => p.id !== id))
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="space-y-3">
      {presets.length === 0 && !showForm && (
        <p className="text-gray-500 text-sm">{t('presets.noPresets')}</p>
      )}

      {presets.map((p) => (
        <div key={p.id} className="bg-gray-800 rounded-lg p-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="font-medium text-white truncate">{p.name}</p>
            <p className="text-xs text-gray-400 mt-0.5">
              {p.model}{p.language ? ` · ${p.language}` : ''}{p.hotwords ? ` · ${p.hotwords}` : ''}
            </p>
          </div>
          <div className="flex gap-2 shrink-0">
            <button onClick={() => openEdit(p)} className="text-sm text-blue-400 hover:text-blue-300">
              {t('presets.edit')}
            </button>
            <button onClick={() => handleDelete(p.id)} className="text-sm text-red-400 hover:text-red-300">
              {t('presets.delete')}
            </button>
          </div>
        </div>
      ))}

      {showForm && (
        <div className="bg-gray-800 rounded-lg p-4 space-y-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">{t('presets.name')}</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder={t('presets.namePlaceholder')}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label htmlFor="transcription-preset-language-field" className="block text-xs text-gray-400 mb-1">{t('settings.language')}</label>
            <select
              id="transcription-preset-language-field"
              value={form.language ?? ''}
              onChange={(e) => setForm({ ...form, language: e.target.value || null })}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">{t('languages.auto')}</option>
              {filterEnabledLanguages(LANGUAGES, enabledLanguages).map((code) => (
                <option key={code} value={code}>{t(`languages.${code}`)}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="transcription-preset-model-field" className="block text-xs text-gray-400 mb-1">{t('settings.model')}</label>
            {models.length === 1 ? (() => {
              const m = models[0]
              const label = t(`settings.modelLabels.${m}`, '')
              return (
                <output id="transcription-preset-model-field" className="block w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5">
                  {label ? `${label} (${m})` : m}
                </output>
              )
            })() : (
              <select
                id="transcription-preset-model-field"
                value={form.model ?? defaultModel}
                onChange={(e) => setForm({ ...form, model: e.target.value })}
                className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
              >
                {models.map((m) => (
                  <option key={m} value={m}>{t(`settings.modelLabels.${m}`, { defaultValue: m })}</option>
                ))}
              </select>
            )}
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">{t('settings.hotwords')}</label>
            <input
              type="text"
              value={form.hotwords ?? ''}
              onChange={(e) => setForm({ ...form, hotwords: e.target.value || null })}
              placeholder={t('settings.hotwordsHelp')}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">{t('settings.initialPrompt')}</label>
            <textarea
              value={form.initial_prompt ?? ''}
              onChange={(e) => setForm({ ...form, initial_prompt: e.target.value || null })}
              placeholder={t('settings.initialPromptHelp')}
              rows={2}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500 resize-none"
            />
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={handleCancel} className="text-sm text-gray-400 hover:text-white px-3 py-1.5">
              {t('common.cancel')}
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !form.name.trim()}
              className="text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded px-4 py-1.5"
            >
              {saving ? '…' : t('presets.save')}
            </button>
          </div>
        </div>
      )}

      {!showForm && (
        <button
          onClick={openNew}
          className="text-sm text-blue-400 hover:text-blue-300"
        >
          + {t('presets.create')}
        </button>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// AnalysisPresetsList
// ---------------------------------------------------------------------------

const ANALYSIS_TEMPLATES = ['summary', 'protocol', 'agenda', 'custom'] as const

function AnalysisPresetsList() {
  const { t } = useTranslation()
  const presets = useStore((s) => s.analysisPresets)
  const setPresets = useStore((s) => s.setAnalysisPresets)
  const enabledLanguages = useStore((s) => s.config?.enabled_languages) || []

  const emptyForm: AnalysisPresetCreate = { name: '', template: 'summary', custom_prompt: null, language: null }
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<AnalysisPresetCreate>(emptyForm)
  const [saving, setSaving] = useState(false)

  const openNew = () => {
    setEditingId(null)
    setForm(emptyForm)
    setShowForm(true)
  }

  const openEdit = (p: AnalysisPreset) => {
    setEditingId(p.id)
    const language = p.language && !isLanguageEnabled(p.language, enabledLanguages) ? null : p.language
    setForm({ name: p.name, template: p.template, custom_prompt: p.custom_prompt, language })
    setShowForm(true)
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingId(null)
    setForm(emptyForm)
  }

  const handleSave = async () => {
    if (!form.name.trim()) return
    setSaving(true)
    try {
      if (editingId) {
        const updated = await api.updateAnalysisPreset(editingId, form)
        setPresets(presets.map((p) => (p.id === editingId ? updated : p)))
      } else {
        const created = await api.createAnalysisPreset(form)
        setPresets([...presets, created])
      }
      handleCancel()
    } catch (err) {
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm(t('presets.confirmDelete'))) return
    try {
      await api.deleteAnalysisPreset(id)
      setPresets(presets.filter((p) => p.id !== id))
    } catch (err) {
      console.error(err)
    }
  }

  const templateLabel = (tmpl: string | null) => {
    if (!tmpl) return t('analysis.customPrompt')
    if (tmpl === 'summary') return t('analysis.templateSummary')
    if (tmpl === 'protocol') return t('analysis.templateProtocol')
    if (tmpl === 'agenda') return t('analysis.templateAgenda')
    return tmpl
  }

  return (
    <div className="space-y-3">
      {presets.length === 0 && !showForm && (
        <p className="text-gray-500 text-sm">{t('presets.noPresets')}</p>
      )}

      {presets.map((p) => (
        <div key={p.id} className="bg-gray-800 rounded-lg p-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="font-medium text-white truncate">{p.name}</p>
            <p className="text-xs text-gray-400 mt-0.5">
              {templateLabel(p.template)}{p.language ? ` · ${p.language}` : ''}
            </p>
          </div>
          <div className="flex gap-2 shrink-0">
            <button onClick={() => openEdit(p)} className="text-sm text-blue-400 hover:text-blue-300">
              {t('presets.edit')}
            </button>
            <button onClick={() => handleDelete(p.id)} className="text-sm text-red-400 hover:text-red-300">
              {t('presets.delete')}
            </button>
          </div>
        </div>
      ))}

      {showForm && (
        <div className="bg-gray-800 rounded-lg p-4 space-y-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">{t('presets.name')}</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder={t('presets.namePlaceholder')}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">{t('analysis.selectTemplate')}</label>
            <select
              value={form.template ?? 'custom'}
              onChange={(e) => setForm({ ...form, template: e.target.value === 'custom' ? null : e.target.value })}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
            >
              {ANALYSIS_TEMPLATES.map((tmpl) => (
                <option key={tmpl} value={tmpl}>{templateLabel(tmpl === 'custom' ? null : tmpl)}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="analysis-preset-language-field" className="block text-xs text-gray-400 mb-1">{t('settings.language')}</label>
            <select
              id="analysis-preset-language-field"
              value={form.language ?? ''}
              onChange={(e) => setForm({ ...form, language: e.target.value || null })}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">{t('languages.auto')}</option>
              {filterEnabledLanguages(LANGUAGES, enabledLanguages).map((code) => (
                <option key={code} value={code}>{t(`languages.${code}`)}</option>
              ))}
            </select>
          </div>
          {(form.template === null || form.template === 'custom') && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">{t('analysis.customizePrompt')}</label>
              <textarea
                value={form.custom_prompt ?? ''}
                onChange={(e) => setForm({ ...form, custom_prompt: e.target.value || null })}
                rows={3}
                className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500 resize-none"
              />
            </div>
          )}
          <div className="flex gap-2 justify-end">
            <button onClick={handleCancel} className="text-sm text-gray-400 hover:text-white px-3 py-1.5">
              {t('common.cancel')}
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !form.name.trim()}
              className="text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded px-4 py-1.5"
            >
              {saving ? '…' : t('presets.save')}
            </button>
          </div>
        </div>
      )}

      {!showForm && (
        <button onClick={openNew} className="text-sm text-blue-400 hover:text-blue-300">
          + {t('presets.create')}
        </button>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// RefinementPresetsList
// ---------------------------------------------------------------------------

function RefinementPresetsList() {
  const { t } = useTranslation()
  const presets = useStore((s) => s.refinementPresets)
  const setPresets = useStore((s) => s.setRefinementPresets)

  const emptyForm: RefinementPresetCreate = { name: '', context: null }
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<RefinementPresetCreate>(emptyForm)
  const [saving, setSaving] = useState(false)

  const openNew = () => {
    setEditingId(null)
    setForm(emptyForm)
    setShowForm(true)
  }

  const openEdit = (p: RefinementPreset) => {
    setEditingId(p.id)
    setForm({ name: p.name, context: p.context })
    setShowForm(true)
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingId(null)
    setForm(emptyForm)
  }

  const handleSave = async () => {
    if (!form.name.trim()) return
    setSaving(true)
    try {
      if (editingId) {
        const updated = await api.updateRefinementPreset(editingId, form)
        setPresets(presets.map((p) => (p.id === editingId ? updated : p)))
      } else {
        const created = await api.createRefinementPreset(form)
        setPresets([...presets, created])
      }
      handleCancel()
    } catch (err) {
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm(t('presets.confirmDelete'))) return
    try {
      await api.deleteRefinementPreset(id)
      setPresets(presets.filter((p) => p.id !== id))
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="space-y-3">
      {presets.length === 0 && !showForm && (
        <p className="text-gray-500 text-sm">{t('presets.noPresets')}</p>
      )}

      {presets.map((p) => (
        <div key={p.id} className="bg-gray-800 rounded-lg p-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="font-medium text-white truncate">{p.name}</p>
            {p.context && <p className="text-xs text-gray-400 mt-0.5 truncate">{p.context}</p>}
          </div>
          <div className="flex gap-2 shrink-0">
            <button onClick={() => openEdit(p)} className="text-sm text-blue-400 hover:text-blue-300">
              {t('presets.edit')}
            </button>
            <button onClick={() => handleDelete(p.id)} className="text-sm text-red-400 hover:text-red-300">
              {t('presets.delete')}
            </button>
          </div>
        </div>
      ))}

      {showForm && (
        <div className="bg-gray-800 rounded-lg p-4 space-y-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">{t('presets.name')}</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder={t('presets.namePlaceholder')}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">{t('editor.refinementContext')}</label>
            <textarea
              value={form.context ?? ''}
              onChange={(e) => setForm({ ...form, context: e.target.value || null })}
              placeholder={t('editor.refinementContextPlaceholder')}
              rows={3}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500 resize-none"
            />
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={handleCancel} className="text-sm text-gray-400 hover:text-white px-3 py-1.5">
              {t('common.cancel')}
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !form.name.trim()}
              className="text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded px-4 py-1.5"
            >
              {saving ? '…' : t('presets.save')}
            </button>
          </div>
        </div>
      )}

      {!showForm && (
        <button onClick={openNew} className="text-sm text-blue-400 hover:text-blue-300">
          + {t('presets.create')}
        </button>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// BundlesList
// ---------------------------------------------------------------------------

function BundlesList() {
  const { t } = useTranslation()
  const bundles = useStore((s) => s.bundles)
  const setBundles = useStore((s) => s.setBundles)
  const activeBundleId = useStore((s) => s.activeBundleId)
  const setActiveBundleId = useStore((s) => s.setActiveBundleId)
  const transcriptionPresets = useStore((s) => s.transcriptionPresets)
  const analysisPresets = useStore((s) => s.analysisPresets)
  const refinementPresets = useStore((s) => s.refinementPresets)

  const emptyForm: PresetBundleCreate = { name: '', transcription_preset_id: null, analysis_preset_id: null, refinement_preset_id: null }
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<PresetBundleCreate>(emptyForm)
  const [saving, setSaving] = useState(false)

  const openNew = () => {
    setEditingId(null)
    setForm(emptyForm)
    setShowForm(true)
  }

  const openEdit = (b: PresetBundle) => {
    setEditingId(b.id)
    setForm({
      name: b.name,
      transcription_preset_id: b.transcription_preset_id,
      analysis_preset_id: b.analysis_preset_id,
      refinement_preset_id: b.refinement_preset_id,
      translate_language: b.translate_language,
    })
    setShowForm(true)
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingId(null)
    setForm(emptyForm)
  }

  const handleSave = async () => {
    if (!form.name.trim()) return
    setSaving(true)
    try {
      if (editingId) {
        const updated = await api.updateBundle(editingId, form)
        setBundles(bundles.map((b) => (b.id === editingId ? updated : b)))
      } else {
        const created = await api.createBundle(form)
        setBundles([...bundles, created])
      }
      handleCancel()
    } catch (err) {
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm(t('presets.bundle.confirmDelete'))) return
    try {
      await api.deleteBundle(id)
      setBundles(bundles.filter((b) => b.id !== id))
      if (activeBundleId === id) setActiveBundleId(null)
    } catch (err) {
      console.error(err)
    }
  }

  const handleToggleDefault = async (b: PresetBundle) => {
    try {
      if (activeBundleId === b.id) {
        await api.clearDefaultBundle()
        setActiveBundleId(null)
        setBundles(bundles.map((x) => ({ ...x, is_default: false })))
      } else {
        await api.setDefaultBundle(b.id)
        setActiveBundleId(b.id)
        setBundles(bundles.map((x) => ({ ...x, is_default: x.id === b.id })))
      }
    } catch (err) {
      console.error(err)
    }
  }

  const presetName = (
    list: { id: string; name: string }[],
    id: string | null
  ) => (id ? (list.find((p) => p.id === id)?.name ?? id) : null)

  return (
    <div className="space-y-3">
      {bundles.length === 0 && !showForm && (
        <p className="text-gray-500 text-sm">{t('presets.noBundles')}</p>
      )}

      {bundles.map((b) => {
        const tpName = presetName(transcriptionPresets, b.transcription_preset_id)
        const apName = presetName(analysisPresets, b.analysis_preset_id)
        const rpName = presetName(refinementPresets, b.refinement_preset_id)
        const isDefault = activeBundleId === b.id

        return (
          <div key={b.id} className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-white truncate">{b.name}</p>
                  {isDefault && (
                    <span className="text-xs bg-blue-900 text-blue-300 rounded px-1.5 py-0.5">
                      {t('presets.bundle.isDefault')}
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {tpName && (
                    <span className="text-xs bg-gray-700 text-gray-300 rounded px-2 py-0.5">
                      {t('presets.transcription')}: {tpName}
                    </span>
                  )}
                  {apName && (
                    <span className="text-xs bg-gray-700 text-gray-300 rounded px-2 py-0.5">
                      {t('presets.analysis')}: {apName}
                    </span>
                  )}
                  {rpName && (
                    <span className="text-xs bg-gray-700 text-gray-300 rounded px-2 py-0.5">
                      {t('presets.refinement')}: {rpName}
                    </span>
                  )}
                  {b.translate_language && (
                    <span className="text-xs bg-gray-700 text-gray-300 rounded px-2 py-0.5">
                      {t('editor.translate')}: {b.translate_language}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex gap-2 shrink-0 items-center">
                <button
                  onClick={() => handleToggleDefault(b)}
                  className={`text-sm ${isDefault ? 'text-yellow-400 hover:text-yellow-300' : 'text-gray-400 hover:text-yellow-400'}`}
                  title={isDefault ? t('presets.bundle.clearDefault') : t('presets.bundle.setDefault')}
                >
                  ★
                </button>
                <button onClick={() => openEdit(b)} className="text-sm text-blue-400 hover:text-blue-300">
                  {t('presets.edit')}
                </button>
                <button onClick={() => handleDelete(b.id)} className="text-sm text-red-400 hover:text-red-300">
                  {t('presets.delete')}
                </button>
              </div>
            </div>
          </div>
        )
      })}

      {showForm && (
        <div className="bg-gray-800 rounded-lg p-4 space-y-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">{t('presets.name')}</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder={t('presets.namePlaceholder')}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">{t('presets.bundle.selectTranscription')}</label>
            <select
              value={form.transcription_preset_id ?? ''}
              onChange={(e) => setForm({ ...form, transcription_preset_id: e.target.value || null })}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">{t('presets.bundle.none')}</option>
              {transcriptionPresets.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">{t('presets.bundle.selectAnalysis')}</label>
            <select
              value={form.analysis_preset_id ?? ''}
              onChange={(e) => setForm({ ...form, analysis_preset_id: e.target.value || null })}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">{t('presets.bundle.none')}</option>
              {analysisPresets.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">{t('presets.bundle.selectRefinement')}</label>
            <select
              value={form.refinement_preset_id ?? ''}
              onChange={(e) => setForm({ ...form, refinement_preset_id: e.target.value || null })}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">{t('presets.bundle.none')}</option>
              {refinementPresets.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">{t('presets.bundle.translateLanguage')}</label>
            <select
              value={form.translate_language ?? ''}
              onChange={(e) => setForm({ ...form, translate_language: e.target.value || null })}
              className="w-full bg-gray-700 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">{t('presets.bundle.none')}</option>
              {LANGUAGES.map((code) => (
                <option key={code} value={code}>{t(`languages.${code}`)}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={handleCancel} className="text-sm text-gray-400 hover:text-white px-3 py-1.5">
              {t('common.cancel')}
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !form.name.trim()}
              className="text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded px-4 py-1.5"
            >
              {saving ? '…' : t('presets.save')}
            </button>
          </div>
        </div>
      )}

      {!showForm && (
        <button onClick={openNew} className="text-sm text-blue-400 hover:text-blue-300">
          + {t('presets.bundle.create')}
        </button>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// PresetsPage
// ---------------------------------------------------------------------------

type Tab = 'transcription' | 'analysis' | 'refinement' | 'bundles'

export function PresetsPage() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<Tab>('transcription')

  const tabs: { key: Tab; label: string }[] = [
    { key: 'transcription', label: t('presets.transcription') },
    { key: 'analysis', label: t('presets.analysis') },
    { key: 'refinement', label: t('presets.refinement') },
    { key: 'bundles', label: t('presets.bundles') },
  ]

  return (
    <div className="px-6 py-4">
      <h2 className="text-xl font-semibold text-white mb-4">{t('presets.title')}</h2>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-gray-700 mb-5">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === key
                ? 'text-white border-b-2 border-blue-400 -mb-px'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {activeTab === 'transcription' && <TranscriptionPresetsList />}
      {activeTab === 'analysis' && <AnalysisPresetsList />}
      {activeTab === 'refinement' && <RefinementPresetsList />}
      {activeTab === 'bundles' && <BundlesList />}
    </div>
  )
}
