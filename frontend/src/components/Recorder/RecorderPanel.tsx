import { useState, useCallback, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useMediaRecorder, getFileExtension, getPreferredMimeType } from './useMediaRecorder'
import { RecorderControls } from './RecorderControls'
import { AudioLevelMeter } from './AudioLevelMeter'
import { DeviceSelector } from './DeviceSelector'
import { api } from '../../api/client'
import { useStore } from '../../store'
import { formatFileSize } from '../../utils/format'

export function RecorderPanel() {
  const { t } = useTranslation()
  const file = useStore((s) => s.file)
  const setFile = useStore((s) => s.setFile)
  const transcriptionId = useStore((s) => s.transcriptionId)
  const transcriptionTitle = useStore((s) => s.transcriptionTitle)
  const reset = useStore((s) => s.reset)

  const handleDelete = useCallback(async () => {
    if (transcriptionId) {
      try {
        await api.deleteTranscription(transcriptionId)
      } catch (e) {
        console.error('Delete failed:', e)
      }
    }
    reset()
  }, [transcriptionId, reset])

  const [audioDeviceId, setAudioDeviceId] = useState('')
  const [videoDeviceId, setVideoDeviceId] = useState('')
  const [useCamera, setUseCamera] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [captureSystemAudio, setCaptureSystemAudio] = useState(false)
  const [secondAudioDeviceId, setSecondAudioDeviceId] = useState('')

  const handleCaptureSystemAudioChange = useCallback((capture: boolean) => {
    setCaptureSystemAudio(capture)
    if (capture) setUseCamera(false)
    if (!capture) setSecondAudioDeviceId('')
  }, [])

  const { state, blob, stream, duration, error, start, pause, resume, stop, discard } =
    useMediaRecorder({ audioDeviceId, videoDeviceId, useCamera, captureSystemAudio, secondAudioDeviceId })

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

      const fileInfo = await api.uploadRecording(file, useCamera)
      setFile(fileInfo)
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : t('recorder.uploadFailed'))
    } finally {
      setUploading(false)
    }
  }, [blob, useCamera, setFile, t])

  const handleStart = useCallback(async () => {
    // Play a short beep tone to signal recording start
    try {
      const ctx = new AudioContext()
      await ctx.resume()
      const oscillator = ctx.createOscillator()
      const gain = ctx.createGain()
      oscillator.connect(gain)
      gain.connect(ctx.destination)
      oscillator.frequency.value = 880
      gain.gain.value = 0.3
      oscillator.start()
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3)
      oscillator.stop(ctx.currentTime + 0.3)
      setTimeout(() => ctx.close(), 500)
    } catch {
      // Audio cue is best-effort
    }
    await start()
  }, [start])

  const isActive = state === 'recording' || state === 'paused'

  if (file) {
    return (
      <div className="flex items-center gap-4 px-6 py-2 bg-gray-800 border-b border-gray-700 text-sm text-gray-300">
        <span>
          {transcriptionTitle ? <>{transcriptionTitle} <span className="text-gray-500">[{file.original_filename}]</span></> : file.original_filename}
        </span>
        <span className="text-gray-500">({formatFileSize(file.file_size)})</span>
        <button onClick={handleDelete} className="text-red-400 hover:text-red-300">
          {t('upload.deleteFile')}
        </button>
      </div>
    )
  }

  return (
    <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 space-y-4">
      {/* Device selector */}
      {state !== 'stopped' && (
        <DeviceSelector
          useCamera={useCamera}
          onUseCameraChange={setUseCamera}
          audioDeviceId={audioDeviceId}
          onAudioDeviceChange={setAudioDeviceId}
          videoDeviceId={videoDeviceId}
          onVideoDeviceChange={setVideoDeviceId}
          captureSystemAudio={captureSystemAudio}
          onCaptureSystemAudioChange={handleCaptureSystemAudioChange}
          secondAudioDeviceId={secondAudioDeviceId}
          onSecondAudioDeviceChange={setSecondAudioDeviceId}
          disabled={isActive}
        />
      )}

      {/* Video preview or audio level meter */}
      {state !== 'stopped' && (
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
      )}

      {/* Consent reminder */}
      {state === 'idle' && (
        <p className="text-xs text-gray-400 text-center">
          {t('recorder.consentReminder')}
        </p>
      )}

      {/* Controls */}
      <RecorderControls
        state={state}
        duration={duration}
        onStart={handleStart}
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
        <div className="p-4 bg-red-900/30 rounded-lg border border-red-700">
          <div className="flex items-center gap-3">
            <span className="text-red-400 text-lg">!</span>
            <span className="text-red-300 text-sm">{uploadError}</span>
          </div>
        </div>
      )}
    </div>
  )
}
