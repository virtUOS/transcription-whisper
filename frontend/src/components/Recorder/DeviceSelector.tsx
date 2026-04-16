import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { getSystemAudioSupport } from '../../utils/platformDetect'

const systemAudioSupport = getSystemAudioSupport()

const warningKey: Record<string, string> = {
  full: 'recorder.systemAudioWarningFull',
  'tab-only': 'recorder.systemAudioWarningTabOnly',
  'dual-device': 'recorder.systemAudioWarningDualDevice',
  limited: 'recorder.systemAudioWarningLimited',
}

interface DeviceSelectorProps {
  useCamera: boolean
  onUseCameraChange: (useCamera: boolean) => void
  useMicrophone: boolean
  onUseMicrophoneChange: (use: boolean) => void
  audioDeviceId: string
  onAudioDeviceChange: (id: string) => void
  videoDeviceId: string
  onVideoDeviceChange: (id: string) => void
  captureSystemAudio: boolean
  onCaptureSystemAudioChange: (capture: boolean) => void
  secondAudioDeviceId: string
  onSecondAudioDeviceChange: (id: string) => void
  disabled?: boolean
}

export function DeviceSelector({
  useCamera,
  onUseCameraChange,
  useMicrophone,
  onUseMicrophoneChange,
  audioDeviceId,
  onAudioDeviceChange,
  videoDeviceId,
  onVideoDeviceChange,
  captureSystemAudio,
  onCaptureSystemAudioChange,
  secondAudioDeviceId,
  onSecondAudioDeviceChange,
  disabled = false,
}: DeviceSelectorProps) {
  const { t } = useTranslation()
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([])
  const [videoDevices, setVideoDevices] = useState<MediaDeviceInfo[]>([])

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
    // eslint-disable-next-line react-hooks/exhaustive-deps -- runs once per camera toggle, not on every device list change
  }, [useCamera])

  // Auto-select first available second device when dual-device dropdown appears
  useEffect(() => {
    if (systemAudioSupport !== 'dual-device' || !captureSystemAudio) return
    if (secondAudioDeviceId) return // Already selected
    const available = audioDevices.filter((d) => d.deviceId !== audioDeviceId)
    if (available.length > 0) {
      onSecondAudioDeviceChange(available[0].deviceId)
    }
  }, [captureSystemAudio, audioDevices, audioDeviceId, secondAudioDeviceId, onSecondAudioDeviceChange])

  return (
    <div className="flex flex-col gap-3">
      {useMicrophone && (
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
      )}

      {systemAudioSupport === 'unsupported' ? (
        <p className="text-xs text-gray-500">{t('recorder.systemAudioUnsupported')}</p>
      ) : (
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

      {captureSystemAudio && warningKey[systemAudioSupport] && (
        <div className="bg-amber-900/50 border border-amber-700 rounded-lg px-3 py-2 text-xs text-amber-200">
          {t(warningKey[systemAudioSupport])}
        </div>
      )}

      {captureSystemAudio && (
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-300 min-w-24">{t('recorder.useMicrophone')}</label>
          <button
            type="button"
            role="switch"
            aria-checked={useMicrophone}
            onClick={() => onUseMicrophoneChange(!useMicrophone)}
            disabled={disabled}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-50 ${
              useMicrophone ? 'bg-blue-600' : 'bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
                useMicrophone ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      )}

      {captureSystemAudio && useMicrophone && systemAudioSupport === 'dual-device' && (
        <div className="flex items-center gap-3 min-w-0">
          <label className="text-sm text-gray-300 min-w-24 shrink-0">{t('recorder.selectSecondDevice')}</label>
          <select
            value={secondAudioDeviceId}
            onChange={(e) => onSecondAudioDeviceChange(e.target.value)}
            disabled={disabled}
            className="flex-1 min-w-0 bg-gray-700 text-white rounded-lg px-3 py-2 text-sm disabled:opacity-50"
          >
            {audioDevices.filter((d) => d.deviceId !== audioDeviceId).map((d) => (
              <option key={d.deviceId} value={d.deviceId}>
                {d.label || `Device ${d.deviceId.slice(0, 8)}`}
              </option>
            ))}
            {audioDevices.length === 0 && <option value="">—</option>}
          </select>
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
