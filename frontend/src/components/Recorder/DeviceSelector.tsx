import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

interface DeviceSelectorProps {
  useCamera: boolean
  onUseCameraChange: (useCamera: boolean) => void
  audioDeviceId: string
  onAudioDeviceChange: (id: string) => void
  videoDeviceId: string
  onVideoDeviceChange: (id: string) => void
  disabled?: boolean
}

export function DeviceSelector({
  useCamera,
  onUseCameraChange,
  audioDeviceId,
  onAudioDeviceChange,
  videoDeviceId,
  onVideoDeviceChange,
  disabled = false,
}: DeviceSelectorProps) {
  const { t } = useTranslation()
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([])
  const [videoDevices, setVideoDevices] = useState<MediaDeviceInfo[]>([])

  useEffect(() => {
    async function enumerate() {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices()
        setAudioDevices(devices.filter((d) => d.kind === 'audioinput'))
        setVideoDevices(devices.filter((d) => d.kind === 'videoinput'))
      } catch {
        // Permission not yet granted — devices will populate after getUserMedia
      }
    }
    enumerate()
    navigator.mediaDevices.addEventListener('devicechange', enumerate)
    return () => navigator.mediaDevices.removeEventListener('devicechange', enumerate)
  }, [])

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <label className="text-sm text-gray-300 min-w-24">{t('recorder.selectMic')}</label>
        <select
          value={audioDeviceId}
          onChange={(e) => onAudioDeviceChange(e.target.value)}
          disabled={disabled}
          className="flex-1 bg-gray-700 text-white rounded-lg px-3 py-2 text-sm disabled:opacity-50"
        >
          {audioDevices.map((d) => (
            <option key={d.deviceId} value={d.deviceId}>
              {d.label || `Microphone ${d.deviceId.slice(0, 8)}`}
            </option>
          ))}
          {audioDevices.length === 0 && <option value="">—</option>}
        </select>
      </div>

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

      {useCamera && (
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-300 min-w-24">{t('recorder.selectCamera')}</label>
          <select
            value={videoDeviceId}
            onChange={(e) => onVideoDeviceChange(e.target.value)}
            disabled={disabled}
            className="flex-1 bg-gray-700 text-white rounded-lg px-3 py-2 text-sm disabled:opacity-50"
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
