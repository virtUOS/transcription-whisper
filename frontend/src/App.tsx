import { useEffect } from 'react'
import { Header } from './components/Header'
import { FileUpload, SettingsPanel } from './components/FileUpload'
import { ProgressBar } from './components/ProgressBar'
import { TranscriptionList } from './components/TranscriptionList'
import { useStore } from './store'
import { api } from './api/client'

function App() {
  const config = useStore((s) => s.config)
  const setConfig = useStore((s) => s.setConfig)
  const file = useStore((s) => s.file)
  const transcriptionStatus = useStore((s) => s.transcriptionStatus)

  useEffect(() => {
    api.getConfig().then(setConfig).catch(console.error)
  }, [setConfig])

  if (!config) return <div className="min-h-screen bg-gray-900 flex items-center justify-center text-gray-400">Loading...</div>

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Header />
      <FileUpload />
      {file && <SettingsPanel />}
      <ProgressBar />
      {transcriptionStatus === 'completed' && (
        <div className="mx-6 my-4 p-4 bg-gray-800 rounded-lg border border-gray-700 text-green-400 text-sm">
          Transcription complete — editor components coming in Plan 4
        </div>
      )}
      <TranscriptionList />
    </div>
  )
}

export default App
