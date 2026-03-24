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

  const transcriptionId = useStore((s) => s.transcriptionId)

  function switchTab(tab: 'upload' | 'record') {
    if (tab === activeTab && !transcriptionId) return
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
      <div className="flex mx-6 mt-4 mb-4 border-b border-gray-700" role="tablist">
        <button
          role="tab"
          aria-selected={activeTab === 'upload'}
          onClick={() => switchTab('upload')}
          className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
            activeTab === 'upload'
              ? 'border-blue-500 text-white'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          {t('recorder.tabUpload')}
        </button>
        {supportsRecording && (
          <button
            role="tab"
            aria-selected={activeTab === 'record'}
            onClick={() => switchTab('record')}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === 'record'
                ? 'border-blue-500 text-white'
                : 'border-transparent text-gray-400 hover:text-gray-200'
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
