import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { getSystemAudioSupport } from '../../utils/platformDetect'
import { useDevicePermission } from '../../utils/devicePermissions'
import { SourceCard } from './SourceCard'

const systemAudioSupport = getSystemAudioSupport()

const warningKey: Record<string, string> = {
  full: 'recorder.systemAudioWarningFull',
  'tab-only': 'recorder.systemAudioWarningTabOnly',
  'dual-device': 'recorder.systemAudioWarningDualDevice',
  limited: 'recorder.systemAudioWarningLimited',
}

interface RecordingSourcesProps {
  useMicrophone: boolean
  onUseMicrophoneChange: (use: boolean) => void
  audioDeviceId: string
  onAudioDeviceChange: (id: string) => void
  captureSystemAudio: boolean
  onCaptureSystemAudioChange: (capture: boolean) => void
  secondAudioDeviceId: string
  onSecondAudioDeviceChange: (id: string) => void
  useCamera: boolean
  onUseCameraChange: (use: boolean) => void
  videoDeviceId: string
  onVideoDeviceChange: (id: string) => void
  recording?: boolean
  onValidityChange?: (valid: boolean) => void
}

export function RecordingSources(props: RecordingSourcesProps) {
  const {
    useMicrophone, onUseMicrophoneChange,
    audioDeviceId, onAudioDeviceChange,
    captureSystemAudio, onCaptureSystemAudioChange,
    secondAudioDeviceId, onSecondAudioDeviceChange,
    useCamera, onUseCameraChange,
    videoDeviceId, onVideoDeviceChange,
    recording = false,
    onValidityChange,
  } = props
  const { t } = useTranslation()
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([])
  const [videoDevices, setVideoDevices] = useState<MediaDeviceInfo[]>([])

  const micPermission = useDevicePermission('mic')
  const cameraPermission = useDevicePermission('camera')

  const cameraDisabled = captureSystemAudio
  const validMic = useMicrophone && micPermission.state !== 'denied'
  const validCamera = useCamera && !cameraDisabled && cameraPermission.state !== 'denied'
  const valid = validMic || captureSystemAudio || validCamera

  useEffect(() => {
    onValidityChange?.(valid)
  }, [valid, onValidityChange])

  async function enumerateWithPermission(kind: 'audio' | 'video') {
    try {
      const constraints: MediaStreamConstraints =
        kind === 'audio' ? { audio: true } : { video: true }
      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      stream.getTracks().forEach((tr) => tr.stop())
      const devices = await navigator.mediaDevices.enumerateDevices()
      setAudioDevices(devices.filter((d) => d.kind === 'audioinput'))
      setVideoDevices(devices.filter((d) => d.kind === 'videoinput'))
    } catch {
      // Permission denied — the permission hook picks this up via onchange or the next refresh.
    }
  }

  useEffect(() => {
    async function enumerate() {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices()
        const hasAudioLabels = devices.some((d) => d.kind === 'audioinput' && d.label)
        if (!hasAudioLabels) {
          await enumerateWithPermission('audio')
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
    if (!useCamera || cameraDisabled) return
    const hasVideoLabels = videoDevices.some((d) => d.label)
    if (!hasVideoLabels) {
      enumerateWithPermission('video')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- runs once per camera toggle, not on every device list change
  }, [useCamera, cameraDisabled])

  // Auto-select first available second device when dual-device dropdown appears
  useEffect(() => {
    if (systemAudioSupport !== 'dual-device' || !captureSystemAudio) return
    if (secondAudioDeviceId) return
    const available = audioDevices.filter((d) => d.deviceId !== audioDeviceId)
    if (available.length > 0) {
      onSecondAudioDeviceChange(available[0].deviceId)
    }
  }, [captureSystemAudio, audioDevices, audioDeviceId, secondAudioDeviceId, onSecondAudioDeviceChange])

  const makeDeniedBanner = (sourceLabel: string, onRetry: () => void) => (
    <div role="alert" className="bg-red-900/30 border border-red-700 rounded px-3 py-2 text-xs flex items-start gap-3">
      <span className="text-red-400 text-sm" aria-hidden="true">!</span>
      <div className="flex-1 min-w-0">
        <p className="text-red-200">{t('recorder.permissionDenied', { source: sourceLabel })}</p>
        <p className="text-red-400/80 mt-1">{t('recorder.permissionRecovery')}</p>
      </div>
      <button
        onClick={onRetry}
        className="shrink-0 px-2 py-1 bg-red-700 hover:bg-red-600 text-white rounded text-xs"
      >
        {t('recorder.permissionRetry')}
      </button>
    </div>
  )

  return (
    <div className="flex flex-col gap-3">
      <SourceCard
        icon="🎤"
        label={t('recorder.sourceMicrophone')}
        enabled={useMicrophone}
        onToggle={onUseMicrophoneChange}
        recording={recording}
        permission={micPermission.state}
        deniedBanner={makeDeniedBanner(t('recorder.sourceMicrophone'), micPermission.refresh)}
      >
        <div className="flex flex-col gap-1 min-w-0 sm:flex-row sm:items-center sm:gap-3">
          <label className="text-xs text-gray-400 sm:min-w-24 sm:shrink-0">{t('recorder.selectMic')}</label>
          {audioDevices.length === 1 ? (
            <output className="flex-1 min-w-0 bg-gray-700 text-white rounded px-3 py-1.5 text-sm">
              {audioDevices[0].label || `Microphone ${audioDevices[0].deviceId.slice(0, 8)}`}
            </output>
          ) : (
            <select
              value={audioDeviceId}
              onChange={(e) => onAudioDeviceChange(e.target.value)}
              disabled={recording}
              className="flex-1 min-w-0 bg-gray-700 text-white rounded px-3 py-1.5 text-sm disabled:opacity-50"
            >
              {audioDevices.map((d) => (
                <option key={d.deviceId} value={d.deviceId}>
                  {d.label || `Microphone ${d.deviceId.slice(0, 8)}`}
                </option>
              ))}
              {audioDevices.length === 0 && <option value="">—</option>}
            </select>
          )}
        </div>
      </SourceCard>

      {systemAudioSupport !== 'unsupported' && (
        <SourceCard
          icon="🔊"
          label={t('recorder.sourceSystemAudio')}
          enabled={captureSystemAudio}
          onToggle={onCaptureSystemAudioChange}
          recording={recording}
        >
          <div className="flex flex-col gap-2">
            {warningKey[systemAudioSupport] && (
              <div className="bg-amber-900/40 border border-amber-700 rounded px-3 py-2 text-xs text-amber-200">
                {t(warningKey[systemAudioSupport])}
              </div>
            )}
            {systemAudioSupport === 'dual-device' && (() => {
              const secondDeviceCandidates = audioDevices.filter((d) => d.deviceId !== audioDeviceId)
              return (
                <div className="flex flex-col gap-1 min-w-0 sm:flex-row sm:items-center sm:gap-3">
                  <label className="text-xs text-gray-400 sm:min-w-24 sm:shrink-0">{t('recorder.selectSecondDevice')}</label>
                  {secondDeviceCandidates.length === 1 ? (
                    <output className="flex-1 min-w-0 bg-gray-700 text-white rounded px-3 py-1.5 text-sm">
                      {secondDeviceCandidates[0].label || `Device ${secondDeviceCandidates[0].deviceId.slice(0, 8)}`}
                    </output>
                  ) : (
                    <select
                      value={secondAudioDeviceId}
                      onChange={(e) => onSecondAudioDeviceChange(e.target.value)}
                      disabled={recording}
                      className="flex-1 min-w-0 bg-gray-700 text-white rounded px-3 py-1.5 text-sm disabled:opacity-50"
                    >
                      {secondDeviceCandidates.map((d) => (
                        <option key={d.deviceId} value={d.deviceId}>
                          {d.label || `Device ${d.deviceId.slice(0, 8)}`}
                        </option>
                      ))}
                      {secondDeviceCandidates.length === 0 && <option value="">—</option>}
                    </select>
                  )}
                </div>
              )
            })()}
          </div>
        </SourceCard>
      )}

      <SourceCard
        icon="📷"
        label={t('recorder.sourceCamera')}
        enabled={useCamera}
        onToggle={onUseCameraChange}
        disabled={cameraDisabled}
        disabledReason={t('recorder.sourcesCameraDisabledBySystemAudio')}
        recording={recording}
        permission={cameraPermission.state}
        deniedBanner={makeDeniedBanner(t('recorder.sourceCamera'), cameraPermission.refresh)}
      >
        <div className="flex flex-col gap-1 min-w-0 sm:flex-row sm:items-center sm:gap-3">
          <label className="text-xs text-gray-400 sm:min-w-24 sm:shrink-0">{t('recorder.selectCamera')}</label>
          {videoDevices.length === 1 ? (
            <output className="flex-1 min-w-0 bg-gray-700 text-white rounded px-3 py-1.5 text-sm">
              {videoDevices[0].label || `Camera ${videoDevices[0].deviceId.slice(0, 8)}`}
            </output>
          ) : (
            <select
              value={videoDeviceId}
              onChange={(e) => onVideoDeviceChange(e.target.value)}
              disabled={recording}
              className="flex-1 min-w-0 bg-gray-700 text-white rounded px-3 py-1.5 text-sm disabled:opacity-50"
            >
              {videoDevices.map((d) => (
                <option key={d.deviceId} value={d.deviceId}>
                  {d.label || `Camera ${d.deviceId.slice(0, 8)}`}
                </option>
              ))}
              {videoDevices.length === 0 && <option value="">—</option>}
            </select>
          )}
        </div>
      </SourceCard>

      {!valid && (
        <p className="text-xs text-amber-400">{t('recorder.sourcesAtLeastOne')}</p>
      )}
    </div>
  )
}
