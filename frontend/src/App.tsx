import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Header } from './components/Header'
import { SettingsPanel } from './components/FileUpload'
import { FileUpload } from './components/FileUpload'
import { RecorderPanel } from './components/Recorder'
import { ProgressBar } from './components/ProgressBar'
import { TranscriptionList } from './components/TranscriptionList'
import { MediaPlayer } from './components/MediaPlayer'
import { SubtitleEditor } from './components/SubtitleEditor'
import { SpeakerMapping } from './components/SpeakerMapping'
import { FormatViewer } from './components/FormatViewer'
import { TabBar } from './components/TabBar'
import { AnalysisView } from './components/AnalysisView'
import { useStore, setPopStateFlag } from './store'
import { api } from './api/client'
import { PresetsPage } from './components/PresetsPage/PresetsPage'

function BackButton() {
  const { t } = useTranslation()
  const setCurrentView = useStore((s) => s.setCurrentView)

  return (
    <button
      onClick={() => setCurrentView('archive')}
      className="flex items-center gap-1 px-6 py-2 text-sm text-gray-400 hover:text-white"
    >
      &larr; {t('nav.backToTranscriptions')}
    </button>
  )
}

function DetailActions() {
  const { t } = useTranslation()
  const transcriptionId = useStore((s) => s.transcriptionId)
  const history = useStore((s) => s.transcriptionHistory)
  const setHistory = useStore((s) => s.setTranscriptionHistory)
  const setCurrentView = useStore((s) => s.setCurrentView)
  const reset = useStore((s) => s.reset)

  // Ensure history is loaded (may not be if user navigated directly to detail)
  useEffect(() => {
    if (history.length === 0) {
      api.listTranscriptions().then(setHistory).catch(console.error)
    }
  }, [history.length, setHistory])

  const item = history.find((h) => h.id === transcriptionId)
  if (!item) return null

  const handleArchive = async () => {
    const currentHistory = useStore.getState().transcriptionHistory
    setHistory(currentHistory.map((h) =>
      h.id === item.id ? { ...h, archived: true, expires_at: new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString() } : h
    ))
    try {
      const result = await api.archiveTranscription(item.id)
      const updatedHistory = useStore.getState().transcriptionHistory
      setHistory(updatedHistory.map((h) =>
        h.id === item.id ? { ...h, archived: true, expires_at: result.expires_at } : h
      ))
    } catch {
      const revertHistory = useStore.getState().transcriptionHistory
      setHistory(revertHistory.map((h) =>
        h.id === item.id ? { ...h, archived: item.archived, expires_at: item.expires_at } : h
      ))
    }
  }

  const handleDelete = async () => {
    if (!confirm(t('transcription.confirmDelete'))) return
    try {
      await api.deleteTranscription(item.id)
      setHistory(history.filter((h) => h.id !== item.id))
      reset()
      setCurrentView('archive')
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  return (
    <div className="px-6 mt-1 flex items-center gap-3 text-sm">
      {!item.archived ? (
        <button
          onClick={handleArchive}
          className="flex items-center gap-1 text-gray-400 hover:text-blue-400 transition-colors"
          title={t('transcription.archive')}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          {t('transcription.archive')}
        </button>
      ) : (
        <span className="flex items-center gap-1 text-blue-400 text-xs">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          {t('transcription.archived')}
        </span>
      )}
      <button
        onClick={handleDelete}
        className="flex items-center gap-1 text-gray-400 hover:text-red-400 transition-colors"
        title={t('transcription.delete')}
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
        {t('transcription.delete')}
      </button>
      <span className={`text-xs ${new Date(item.expires_at + 'Z').getTime() - Date.now() < 24 * 60 * 60 * 1000 ? 'text-red-400' : 'text-gray-500'}`}>
        {t('transcription.expiresOn', { date: new Date(item.expires_at + 'Z').toLocaleDateString('de-DE') })}
      </span>
    </div>
  )
}

function App() {
  const { t } = useTranslation()
  const config = useStore((s) => s.config)
  const setConfig = useStore((s) => s.setConfig)
  const file = useStore((s) => s.file)
  const uploading = useStore((s) => s.uploading)
  const currentView = useStore((s) => s.currentView)
  const setCurrentView = useStore((s) => s.setCurrentView)
  const transcriptionStatus = useStore((s) => s.transcriptionStatus)
  const transcriptionTitle = useStore((s) => s.transcriptionTitle)
  const transcriptionResult = useStore((s) => s.transcriptionResult)
  const activeTab = useStore((s) => s.activeTab)
  const [speakerModalOpen, setSpeakerModalOpen] = useState(false)
  const [focusSpeaker, setFocusSpeaker] = useState<string | undefined>(undefined)
  const [playerCollapsed, setPlayerCollapsed] = useState(false)

  useEffect(() => {
    setPlayerCollapsed(false)
  }, [file?.id])

  const handleOpenSpeakerModal = (speakerId?: string) => {
    setFocusSpeaker(speakerId)
    setSpeakerModalOpen(true)
  }

  const setTranscriptionPresets = useStore((s) => s.setTranscriptionPresets)
  const setAnalysisPresets = useStore((s) => s.setAnalysisPresets)
  const setRefinementPresets = useStore((s) => s.setRefinementPresets)
  const setBundles = useStore((s) => s.setBundles)
  const setActiveBundleId = useStore((s) => s.setActiveBundleId)

  useEffect(() => {
    api.getConfig().then(setConfig).catch(console.error)
    Promise.all([
      api.getTranscriptionPresets(),
      api.getAnalysisPresets(),
      api.getRefinementPresets(),
      api.getBundles(),
      api.getDefaultBundle(),
    ]).then(([tp, ap, rp, bundles, defaultBundle]) => {
      setTranscriptionPresets(tp)
      setAnalysisPresets(ap)
      setRefinementPresets(rp)
      setBundles(bundles)
      if (defaultBundle) setActiveBundleId(defaultBundle.id)
    }).catch(console.error)
  }, [setConfig, setTranscriptionPresets, setAnalysisPresets, setRefinementPresets, setBundles, setActiveBundleId])

  // Track whether current navigation was triggered by browser back/forward
  const isPopStateNav = useRef(false)

  // Sync browser back/forward buttons with view state
  useEffect(() => {
    const handlePopState = (e: PopStateEvent) => {
      setPopStateFlag(true)
      isPopStateNav.current = true
      setCurrentView(e.state?.view ?? 'archive')
      setPopStateFlag(false)
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [setCurrentView])

  // Update browser tab title based on current view
  useEffect(() => {
    if (currentView === 'detail' && file) {
      document.title = `${transcriptionTitle || file.original_filename} — ${t('title')}`
    } else {
      document.title = t('title')
    }
  }, [currentView, file, t])

  const setRefinedUtterances = useStore((s) => s.setRefinedUtterances)
  const setRefinementMetadata = useStore((s) => s.setRefinementMetadata)
  const setActiveView = useStore((s) => s.setActiveView)
  const addAnalysis = useStore((s) => s.addAnalysis)
  const setTranslatedUtterances = useStore((s) => s.setTranslatedUtterances)
  const setTranslationLanguage = useStore((s) => s.setTranslationLanguage)
  const autoPipelineRanRef = useRef(false)
  const [pipelineStatus, setPipelineStatus] = useState<{ key: string; step: 'refine' | 'analyze' | 'translate'; params?: Record<string, string> } | null>(null)
  const [pipelineErrors, setPipelineErrors] = useState<string[]>([])

  // Reset auto-pipeline flag when a new transcription starts
  useEffect(() => {
    if (transcriptionStatus && transcriptionStatus !== 'completed') {
      autoPipelineRanRef.current = false
      setPipelineStatus(null)
      setPipelineErrors([])
    }
  }, [transcriptionStatus])

  // Auto-navigate to detail view when transcription completes
  useEffect(() => {
    if (isPopStateNav.current) {
      isPopStateNav.current = false
      return
    }
    if (transcriptionStatus === 'completed' && transcriptionResult && (currentView === 'upload' || currentView === 'record')) {
      setCurrentView('detail')
    }
  }, [transcriptionStatus, transcriptionResult, currentView, setCurrentView])

  // Auto-run refinement & analysis when transcription completes with an active bundle
  useEffect(() => {
    if (transcriptionStatus !== 'completed' || !transcriptionResult || autoPipelineRanRef.current) return
    const bundleId = useStore.getState().activeBundleId
    if (!bundleId) return
    const bundles = useStore.getState().bundles
    const bundle = bundles.find((b) => b.id === bundleId)
    if (!bundle) return

    const transcriptionId = useStore.getState().transcriptionId
    if (!transcriptionId) return

    const refinementPresets = useStore.getState().refinementPresets
    const analysisPresets = useStore.getState().analysisPresets
    const hasRefinement = bundle.refinement_preset_id && refinementPresets.find((p) => p.id === bundle.refinement_preset_id)
    const hasAnalysis = bundle.analysis_preset_id && analysisPresets.find((p) => p.id === bundle.analysis_preset_id)
    const hasTranslation = bundle.translate_language

    if (!hasRefinement && !hasAnalysis && !hasTranslation) return
    autoPipelineRanRef.current = true

    const run = async () => {
      const errors: string[] = []

      if (hasRefinement) {
        setPipelineStatus({ key: 'editor.refining', step: 'refine' })
        try {
          const result = await api.generateRefinement(transcriptionId, hasRefinement.context || undefined)
          setRefinedUtterances(result.utterances)
          setRefinementMetadata(result.metadata)
          setActiveView('refined')
        } catch (e) {
          errors.push(`${t('editor.refineTranscription')}: ${e instanceof Error ? e.message : String(e)}`)
        }
      }

      if (hasAnalysis) {
        setPipelineStatus({ key: 'analysis.generating', step: 'analyze' })
        try {
          const result = await api.generateAnalysis(transcriptionId, {
            template: hasAnalysis.template,
            custom_prompt: hasAnalysis.custom_prompt,
            language: hasAnalysis.language,
            chapter_hints: hasAnalysis.chapter_hints,
            agenda: hasAnalysis.agenda,
          })
          const analysisResult = result as { id: string; template?: string; language?: string; llm_provider?: string; llm_model?: string; created_at?: string }
          addAnalysis({
            id: analysisResult.id,
            template: analysisResult.template || null,
            language: analysisResult.language || null,
            llm_provider: analysisResult.llm_provider || null,
            llm_model: analysisResult.llm_model || null,
            created_at: analysisResult.created_at || null,
          })
        } catch (e) {
          errors.push(`${t('editor.analysis')}: ${e instanceof Error ? e.message : String(e)}`)
        }
      }

      if (hasTranslation) {
        setPipelineStatus({ key: 'pipeline.translating', step: 'translate', params: { language: t(`languages.${hasTranslation}`) } })
        try {
          const result = await api.translateTranscription(transcriptionId, hasTranslation)
          setTranslatedUtterances(result.utterances)
          setTranslationLanguage(result.language)
        } catch (e) {
          errors.push(`${t('editor.translate')}: ${e instanceof Error ? e.message : String(e)}`)
        }
      }

      setPipelineStatus(null)
      if (errors.length > 0) setPipelineErrors(errors)
    }

    run()
  }, [transcriptionStatus, transcriptionResult, setRefinedUtterances, setRefinementMetadata, setActiveView, addAnalysis, setTranslatedUtterances, setTranslationLanguage])

  if (!config) return <div className="min-h-screen bg-gray-900 flex items-center justify-center text-gray-400">{t('common.loading')}</div>

  const showEditor = transcriptionStatus === 'completed' && transcriptionResult

  return (
    <div className="min-h-screen bg-gray-900 text-white max-w-[1200px] mx-auto overflow-x-hidden">
      <Header />

      {currentView === 'archive' && (
        <TranscriptionList />
      )}

      {currentView === 'presets' && (
        <>
          <BackButton />
          <PresetsPage />
        </>
      )}

      {currentView === 'upload' && (
        <>
          <BackButton />
          <FileUpload />
          {(file || uploading) && !showEditor && <SettingsPanel />}
          <ProgressBar />
        </>
      )}

      {currentView === 'record' && (
        <>
          <BackButton />
          <RecorderPanel />
          {(file || uploading) && !showEditor && <SettingsPanel />}
          <ProgressBar />
        </>
      )}

      {currentView === 'detail' && (
        <>
          <BackButton />
          {file && (
            <h1 className="px-6 text-lg font-semibold text-white truncate">
              {transcriptionTitle || file.original_filename}
              {transcriptionTitle && (
                <span className="text-sm font-normal text-gray-500 ml-2">[{file.original_filename}]</span>
              )}
            </h1>
          )}
          <DetailActions />
          <ProgressBar />
          {pipelineStatus && (
            <div className={`mx-6 my-2 px-4 py-2 rounded-lg flex items-center gap-3 ${
              pipelineStatus.step === 'refine' ? 'bg-amber-900/30 border border-amber-700/50' :
              pipelineStatus.step === 'translate' ? 'bg-purple-900/30 border border-purple-700/50' :
              'bg-blue-900/30 border border-blue-700/50'
            }`}>
              <div className={`animate-spin h-4 w-4 border-2 border-t-transparent rounded-full shrink-0 ${
                pipelineStatus.step === 'refine' ? 'border-amber-400' :
                pipelineStatus.step === 'translate' ? 'border-purple-400' :
                'border-blue-400'
              }`} />
              <span className={`text-sm ${
                pipelineStatus.step === 'refine' ? 'text-amber-200' :
                pipelineStatus.step === 'translate' ? 'text-purple-200' :
                'text-blue-200'
              }`}>{t(pipelineStatus.key, pipelineStatus.params)}</span>
            </div>
          )}
          {pipelineErrors.length > 0 && (
            <div className="mx-6 my-2 px-4 py-2 bg-red-900/30 rounded-lg border border-red-700/50">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-red-300 text-sm font-medium mb-1">{t('pipeline.errors')}</p>
                  {pipelineErrors.map((err, i) => (
                    <p key={i} className="text-red-400/80 text-xs">{err}</p>
                  ))}
                </div>
                <button
                  onClick={() => setPipelineErrors([])}
                  className="text-red-400 hover:text-red-300 text-sm shrink-0 mt-0.5"
                >
                  ✕
                </button>
              </div>
            </div>
          )}
          {showEditor && file && (
            <>
              <MediaPlayer
                fileId={file.id}
                mediaType={file.media_type}
                hasVideo={file.has_video}
                onCollapsedChange={setPlayerCollapsed}
              />
              <TabBar onSpeakerNamesClick={() => handleOpenSpeakerModal()} />

              <div className={`mx-6 my-2 ${!file.has_video || playerCollapsed ? 'max-h-[calc(100vh-14rem)]' : 'max-h-[calc(100vh-22rem)]'} overflow-auto`}>
                {activeTab === 'subtitles' && <SubtitleEditor onOpenSpeakerModal={handleOpenSpeakerModal} />}
                {activeTab === 'analysis' && <AnalysisView />}
                {['srt', 'vtt', 'json', 'txt'].includes(activeTab) && (
                  <FormatViewer format={activeTab} />
                )}
              </div>

              <SpeakerMapping isOpen={speakerModalOpen} onClose={() => { setSpeakerModalOpen(false); setFocusSpeaker(undefined) }} focusSpeaker={focusSpeaker} />
            </>
          )}
        </>
      )}
    </div>
  )
}

export default App
