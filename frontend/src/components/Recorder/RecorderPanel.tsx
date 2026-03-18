import { useState, useCallback, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useMediaRecorder, getFileExtension, getPreferredMimeType } from './useMediaRecorder'
import { RecorderControls } from './RecorderControls'
import { AudioLevelMeter } from './AudioLevelMeter'
import { DeviceSelector } from './DeviceSelector'
import { api } from '../../api/client'
import { useStore } from '../../store'

export function RecorderPanel() {
  const { t } = useTranslation()
  const setFile = useStore((s) => s.setFile)

  const [audioDeviceId, setAudioDeviceId] = useState('')
  const [videoDeviceId, setVideoDeviceId] = useState('')
  const [useCamera, setUseCamera] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const { state, blob, stream, duration, error, start, pause, resume, stop, discard } =
    useMediaRecorder({ audioDeviceId, videoDeviceId, useCamera })

  const videoPreviewRef = useRef<HTMLVideoElement>(null)

  // Webcam preview
  useEffect(() => {
    if (videoPreviewRef.current && stream && useCamera) {
      videoPreviewRef.current.srcObject = stream
    }
  }, [stream, useCamera])

  // beforeunload warning
  useEffect(() => {
    const shouldWarn = state === 'recording' || state === 'paused' || (state === 'stopped' && blob)
    if (!shouldWarn) return

    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault()
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [state, blob])

  const handleUseRecording = useCallback(async () => {
    if (!blob) return
    setUploading(true)
    setUploadError(null)

    try {
      const mimeType = blob.type || getPreferredMimeType(useCamera)
      const ext = getFileExtension(mimeType)
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
      const filename = `recording-${timestamp}.${ext}`
      const file = new File([blob], filename, { type: mimeType })

      const fileInfo = await api.uploadFile(file)
      setFile(fileInfo)
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : t('recorder.uploadFailed'))
    } finally {
      setUploading(false)
    }
  }, [blob, useCamera, setFile, t])

  const isActive = state === 'recording' || state === 'paused'

  return (
    <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 space-y-4">
      {/* Device selector */}
      <DeviceSelector
        useCamera={useCamera}
        onUseCameraChange={setUseCamera}
        audioDeviceId={audioDeviceId}
        onAudioDeviceChange={setAudioDeviceId}
        videoDeviceId={videoDeviceId}
        onVideoDeviceChange={setVideoDeviceId}
        disabled={isActive}
      />

      {/* Video preview or audio level meter */}
      <div className="flex justify-center">
        {useCamera && stream ? (
          <video
            ref={videoPreviewRef}
            autoPlay
            muted
            playsInline
            className="w-full max-w-md rounded-lg bg-black"
            style={{ maxHeight: '240px' }}
          />
        ) : (
          <div className="w-full max-w-md">
            <AudioLevelMeter stream={stream} />
          </div>
        )}
      </div>

      {/* Controls */}
      <RecorderControls
        state={state}
        duration={duration}
        onStart={start}
        onPause={pause}
        onResume={resume}
        onStop={stop}
        onDiscard={discard}
        onUseRecording={handleUseRecording}
        uploading={uploading}
      />

      {/* Error messages */}
      {error && (
        <p className="text-red-400 text-sm text-center">{t(`recorder.${error}`)}</p>
      )}
      {uploadError && (
        <p className="text-red-400 text-sm text-center">{uploadError}</p>
      )}
    </div>
  )
}
