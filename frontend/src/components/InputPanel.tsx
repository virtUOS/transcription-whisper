import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { FileUpload } from './FileUpload'
import { RecorderPanel } from './Recorder'
import { useStore } from '../store'

export function InputPanel() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<'upload' | 'record'>('upload')
  const supportsRecording = typeof MediaRecorder !== 'undefined'
  const file = useStore((s) => s.file)
  const unsavedEdits = useStore((s) => s.unsavedEdits)
  const reset = useStore((s) => s.reset)

  function switchTab(tab: 'upload' | 'record') {
    if (tab === activeTab) return
    if (file) {
      if (unsavedEdits) {
        if (!window.confirm(t('recorder.unsavedSwitchTab'))) return
      }
      reset()
    }
    setActiveTab(tab)
  }

  return (
    <div>
      <div className="flex gap-2 mx-6 mt-4 mb-4">
        <button
          onClick={() => switchTab('upload')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'upload'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          {t('recorder.tabUpload')}
        </button>
        {supportsRecording && (
          <button
            onClick={() => switchTab('record')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'record'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {t('recorder.tabRecord')}
          </button>
        )}
      </div>
      {activeTab === 'upload' ? <FileUpload /> : <RecorderPanel />}
    </div>
  )
}
