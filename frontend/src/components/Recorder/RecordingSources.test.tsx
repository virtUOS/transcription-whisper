import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import i18n from '../../i18n'
import { RecordingSources } from './RecordingSources'

const permission = vi.hoisted(() => ({ mic: 'granted' }))

vi.mock('../../utils/devicePermissions', () => ({
  useDevicePermission: (kind: string) => ({
    state: kind === 'mic' ? permission.mic : 'granted',
    refresh: vi.fn(),
  }),
}))

vi.mock('../../utils/platformDetect', () => ({
  getSystemAudioSupport: () => 'full',
}))

const camera = { kind: 'videoinput', deviceId: 'cam1', label: 'Cam' }
const mic = { kind: 'audioinput', deviceId: 'mic1', label: 'Mic' }

beforeEach(async () => {
  permission.mic = 'granted'
  await i18n.changeLanguage('en')
  Object.defineProperty(navigator, 'mediaDevices', {
    configurable: true,
    value: {
      enumerateDevices: vi.fn().mockResolvedValue([mic, camera]),
      getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [] }),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    },
  })
})

function renderSources(overrides: Partial<React.ComponentProps<typeof RecordingSources>>) {
  const onValidityChange = vi.fn()
  render(
    <RecordingSources
      useMicrophone={false}
      onUseMicrophoneChange={vi.fn()}
      audioDeviceId=""
      onAudioDeviceChange={vi.fn()}
      captureSystemAudio={false}
      onCaptureSystemAudioChange={vi.fn()}
      secondAudioDeviceId=""
      onSecondAudioDeviceChange={vi.fn()}
      useCamera={false}
      onUseCameraChange={vi.fn()}
      videoDeviceId=""
      onVideoDeviceChange={vi.fn()}
      onValidityChange={onValidityChange}
      {...overrides}
    />,
  )
  return onValidityChange
}

describe('RecordingSources validity', () => {
  it('camera alone is not a valid source', async () => {
    const onValidityChange = renderSources({ useCamera: true })
    await waitFor(() => expect(onValidityChange).toHaveBeenLastCalledWith(false))
    expect(screen.getByText('Turn on the microphone or system audio.')).toBeInTheDocument()
  })

  it('microphone with camera is valid', async () => {
    const onValidityChange = renderSources({ useMicrophone: true, useCamera: true })
    await waitFor(() => expect(onValidityChange).toHaveBeenLastCalledWith(true))
    expect(screen.queryByText('Turn on the microphone or system audio.')).toBeNull()
  })

  it('system audio without microphone is valid', async () => {
    const onValidityChange = renderSources({ captureSystemAudio: true })
    await waitFor(() => expect(onValidityChange).toHaveBeenLastCalledWith(true))
  })

  it('blocked microphone is invalid but does not claim the microphone is off', async () => {
    permission.mic = 'denied'
    const onValidityChange = renderSources({ useMicrophone: true })
    await waitFor(() => expect(onValidityChange).toHaveBeenLastCalledWith(false))
    expect(screen.queryByText('Turn on the microphone or system audio.')).toBeNull()
  })
})
