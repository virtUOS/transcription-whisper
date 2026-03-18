import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { FileUpload } from './FileUpload'
import { RecorderPanel } from './Recorder'

export function InputPanel() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<'upload' | 'record'>('upload')
  const supportsRecording = typeof MediaRecorder !== 'undefined'

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setActiveTab('upload')}
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
            onClick={() => setActiveTab('record')}
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
