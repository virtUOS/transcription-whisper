import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

interface DeviceSelectorProps {
  useCamera: boolean
  onUseCameraChange: (useCamera: boolean) => void
  audioDeviceId: string
  onAudioDeviceChange: (id: string) => void
  videoDeviceId: string
  onVideoDeviceChange: (id: string) => void
  captureSystemAudio: boolean
  onCaptureSystemAudioChange: (capture: boolean) => void
  disabled?: boolean
}

export function DeviceSelector({
  useCamera,
  onUseCameraChange,
  audioDeviceId,
  onAudioDeviceChange,
  videoDeviceId,
  onVideoDeviceChange,
  captureSystemAudio,
  onCaptureSystemAudioChange,
  disabled = false,
}: DeviceSelectorProps) {
  const { t } = useTranslation()
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([])
  const [videoDevices, setVideoDevices] = useState<MediaDeviceInfo[]>([])

  const supportsDisplayMedia = typeof navigator.mediaDevices?.getDisplayMedia === 'function'

  async function enumerateWithPermission(requestVideo: boolean) {
    try {
      const constraints: MediaStreamConstraints = { audio: true }
      if (requestVideo) constraints.video = true
      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      stream.getTracks().forEach((t) => t.stop())
      const devices = await navigator.mediaDevices.enumerateDevices()
      setAudioDevices(devices.filter((d) => d.kind === 'audioinput'))
      setVideoDevices(devices.filter((d) => d.kind === 'videoinput'))
    } catch {
      // Permission denied
    }
  }

  useEffect(() => {
    async function enumerate() {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices()
        const hasAudioLabels = devices.some((d) => d.kind === 'audioinput' && d.label)
        if (!hasAudioLabels) {
          await enumerateWithPermission(false)
        } else {
          setAudioDevices(devices.filter((d) => d.kind === 'audioinput'))
          setVideoDevices(devices.filter((d) => d.kind === 'videoinput'))
        }
      } catch {
        // Permission denied — show empty list
      }
    }
    enumerate()
    navigator.mediaDevices.addEventListener('devicechange', enumerate)
    return () => navigator.mediaDevices.removeEventListener('devicechange', enumerate)
  }, [])

  useEffect(() => {
    if (!useCamera) return
    const hasVideoLabels = videoDevices.some((d) => d.label)
    if (!hasVideoLabels) {
      enumerateWithPermission(true)
    }
  }, [useCamera])

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3 min-w-0">
        <label className="text-sm text-gray-300 min-w-24 shrink-0">{t('recorder.selectMic')}</label>
        <select
          value={audioDeviceId}
          onChange={(e) => onAudioDeviceChange(e.target.value)}
          disabled={disabled}
          className="flex-1 min-w-0 bg-gray-700 text-white rounded-lg px-3 py-2 text-sm disabled:opacity-50"
        >
          {audioDevices.map((d) => (
            <option key={d.deviceId} value={d.deviceId}>
              {d.label || `Microphone ${d.deviceId.slice(0, 8)}`}
            </option>
          ))}
          {audioDevices.length === 0 && <option value="">—</option>}
        </select>
      </div>

      {supportsDisplayMedia && (
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-300 min-w-24">{t('recorder.systemAudio')}</label>
          <button
            type="button"
            role="switch"
            aria-checked={captureSystemAudio}
            onClick={() => onCaptureSystemAudioChange(!captureSystemAudio)}
            disabled={disabled}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-50 ${
              captureSystemAudio ? 'bg-blue-600' : 'bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
                captureSystemAudio ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      )}

      {captureSystemAudio && (
        <div className="bg-amber-900/50 border border-amber-700 rounded-lg px-3 py-2 text-xs text-amber-200">
          {t('recorder.systemAudioWarning')}
        </div>
      )}

      {!captureSystemAudio && (
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-300 min-w-24">{t('recorder.useCamera')}</label>
          <button
            type="button"
            role="switch"
            aria-checked={useCamera}
            onClick={() => onUseCameraChange(!useCamera)}
            disabled={disabled}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-50 ${
              useCamera ? 'bg-blue-600' : 'bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
                useCamera ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      )}

      {!captureSystemAudio && useCamera && (
        <div className="flex items-center gap-3 min-w-0">
          <label className="text-sm text-gray-300 min-w-24 shrink-0">{t('recorder.selectCamera')}</label>
          <select
            value={videoDeviceId}
            onChange={(e) => onVideoDeviceChange(e.target.value)}
            disabled={disabled}
            className="flex-1 min-w-0 bg-gray-700 text-white rounded-lg px-3 py-2 text-sm disabled:opacity-50"
          >
            {videoDevices.map((d) => (
              <option key={d.deviceId} value={d.deviceId}>
                {d.label || `Camera ${d.deviceId.slice(0, 8)}`}
              </option>
            ))}
            {videoDevices.length === 0 && <option value="">—</option>}
          </select>
        </div>
      )}
    </div>
  )
}
