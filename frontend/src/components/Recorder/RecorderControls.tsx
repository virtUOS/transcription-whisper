import { useTranslation } from 'react-i18next'
import type { RecorderState } from './useMediaRecorder'

interface RecorderControlsProps {
  state: RecorderState
  duration: number
  onStart: () => void
  onPause: () => void
  onResume: () => void
  onStop: () => void
  onDiscard: () => void
  onUseRecording: () => void
  uploading?: boolean
  startDisabled?: boolean
  startDisabledReason?: string
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000)
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60
  return [h, m, s].map((v) => String(v).padStart(2, '0')).join(':')
}

export function RecorderControls({
  state,
  duration,
  onStart,
  onPause,
  onResume,
  onStop,
  onDiscard,
  onUseRecording,
  uploading = false,
  startDisabled = false,
  startDisabledReason,
}: RecorderControlsProps) {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Timer */}
      {state !== 'idle' && (
        <div className="text-3xl font-mono text-white tabular-nums">
          {formatDuration(duration)}
          {state === 'recording' && (
            <span className="inline-block w-3 h-3 rounded-full bg-red-500 ml-3 animate-pulse" />
          )}
        </div>
      )}

      {/* Buttons */}
      <div className="flex gap-3">
        {state === 'idle' && (
          <button
            onClick={onStart}
            disabled={startDisabled}
            title={startDisabled ? startDisabledReason : undefined}
            className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
          >
            <span className="w-3 h-3 rounded-full bg-white" />
            {t('recorder.startRecording')}
          </button>
        )}

        {state === 'recording' && (
          <>
            <button
              onClick={onPause}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg text-sm transition-colors"
            >
              {t('recorder.pause')}
            </button>
            <button
              onClick={onStop}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
            >
              {t('recorder.stop')}
            </button>
            <button
              onClick={onDiscard}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-red-400 rounded-lg text-sm transition-colors"
            >
              {t('recorder.discard')}
            </button>
          </>
        )}

        {state === 'paused' && (
          <>
            <button
              onClick={onResume}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm transition-colors"
            >
              {t('recorder.resume')}
            </button>
            <button
              onClick={onStop}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
            >
              {t('recorder.stop')}
            </button>
            <button
              onClick={onDiscard}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-red-400 rounded-lg text-sm transition-colors"
            >
              {t('recorder.discard')}
            </button>
          </>
        )}

        {state === 'stopped' && (
          <>
            <button
              onClick={onUseRecording}
              disabled={uploading}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
            >
              {uploading ? t('recorder.uploading') : t('recorder.useRecording')}
            </button>
            <button
              onClick={onDiscard}
              disabled={uploading}
              className="px-6 py-3 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-red-400 rounded-lg font-medium transition-colors"
            >
              {t('recorder.discard')}
            </button>
          </>
        )}
      </div>
    </div>
  )
}
