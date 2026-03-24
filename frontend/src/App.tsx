import { useEffect, useState } from 'react'
import { Header } from './components/Header'
import { SettingsPanel } from './components/FileUpload'
import { InputPanel } from './components/InputPanel'
import { ProgressBar } from './components/ProgressBar'
import { TranscriptionList } from './components/TranscriptionList'
import { MediaPlayer } from './components/MediaPlayer'
import { SubtitleEditor } from './components/SubtitleEditor'
import { SpeakerMapping } from './components/SpeakerMapping'
import { FormatViewer } from './components/FormatViewer'
import { TabBar } from './components/TabBar'
import { SummaryView } from './components/SummaryView'
import { ProtocolView } from './components/ProtocolView'
import { useStore } from './store'
import { api } from './api/client'

function App() {
  const config = useStore((s) => s.config)
  const setConfig = useStore((s) => s.setConfig)
  const file = useStore((s) => s.file)
  const transcriptionStatus = useStore((s) => s.transcriptionStatus)
  const transcriptionResult = useStore((s) => s.transcriptionResult)
  const activeTab = useStore((s) => s.activeTab)
  const [speakerModalOpen, setSpeakerModalOpen] = useState(false)

  useEffect(() => {
    api.getConfig().then(setConfig).catch(console.error)
  }, [setConfig])

  if (!config) return <div className="min-h-screen bg-gray-900 flex items-center justify-center text-gray-400">Loading...</div>

  const showEditor = transcriptionStatus === 'completed' && transcriptionResult

  return (
    <div className="min-h-screen bg-gray-900 text-white max-w-[1200px] mx-auto">
      <Header />
      <InputPanel />
      {file && !showEditor && <SettingsPanel />}
      <ProgressBar />

      {showEditor && file && (
        <>
          <MediaPlayer fileId={file.id} mediaType={file.media_type} />
          <TabBar onSpeakerNamesClick={() => setSpeakerModalOpen(true)} />

          <div className="mx-6 my-2">
            {activeTab === 'subtitles' && <SubtitleEditor />}
            {activeTab === 'summary' && <SummaryView />}
            {activeTab === 'protocol' && <ProtocolView />}
            {['srt', 'vtt', 'json', 'txt'].includes(activeTab) && (
              <FormatViewer format={activeTab} />
            )}
          </div>

          <SpeakerMapping isOpen={speakerModalOpen} onClose={() => setSpeakerModalOpen(false)} />
        </>
      )}

      {!showEditor && <TranscriptionList />}
    </div>
  )
}

export default App
