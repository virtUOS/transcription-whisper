import { useEffect, useState } from 'react'
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
import { useStore } from './store'
import { api } from './api/client'

function BackButton() {
  const { t } = useTranslation()
  const setCurrentView = useStore((s) => s.setCurrentView)

  return (
    <button
      onClick={() => setCurrentView('archive')}
      className="flex items-center gap-1 px-6 py-2 text-sm text-gray-400 hover:text-white"
    >
      &larr; {t('nav.backToRecordings')}
    </button>
  )
}

function App() {
  const { t } = useTranslation()
  const config = useStore((s) => s.config)
  const setConfig = useStore((s) => s.setConfig)
  const file = useStore((s) => s.file)
  const currentView = useStore((s) => s.currentView)
  const setCurrentView = useStore((s) => s.setCurrentView)
  const transcriptionStatus = useStore((s) => s.transcriptionStatus)
  const transcriptionResult = useStore((s) => s.transcriptionResult)
  const activeTab = useStore((s) => s.activeTab)
  const [speakerModalOpen, setSpeakerModalOpen] = useState(false)
  const [focusSpeaker, setFocusSpeaker] = useState<string | undefined>(undefined)

  const handleOpenSpeakerModal = (speakerId?: string) => {
    setFocusSpeaker(speakerId)
    setSpeakerModalOpen(true)
  }

  useEffect(() => {
    api.getConfig().then(setConfig).catch(console.error)
  }, [setConfig])

  // Auto-navigate to detail view when transcription completes
  useEffect(() => {
    if (transcriptionStatus === 'completed' && transcriptionResult && (currentView === 'upload' || currentView === 'record')) {
      setCurrentView('detail')
    }
  }, [transcriptionStatus, transcriptionResult, currentView, setCurrentView])

  if (!config) return <div className="min-h-screen bg-gray-900 flex items-center justify-center text-gray-400">{t('common.loading')}</div>

  const showEditor = transcriptionStatus === 'completed' && transcriptionResult

  return (
    <div className="min-h-screen bg-gray-900 text-white max-w-[1200px] mx-auto overflow-x-hidden">
      <Header />

      {currentView === 'archive' && (
        <TranscriptionList />
      )}

      {currentView === 'upload' && (
        <>
          <BackButton />
          <FileUpload />
          {file && !showEditor && <SettingsPanel />}
          <ProgressBar />
        </>
      )}

      {currentView === 'record' && (
        <>
          <BackButton />
          <RecorderPanel />
          <ProgressBar />
        </>
      )}

      {currentView === 'detail' && (
        <>
          <BackButton />
          <ProgressBar />
          {showEditor && file && (
            <>
              <MediaPlayer fileId={file.id} mediaType={file.media_type} />
              <TabBar onSpeakerNamesClick={() => handleOpenSpeakerModal()} />

              <div className="mx-6 my-2">
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
