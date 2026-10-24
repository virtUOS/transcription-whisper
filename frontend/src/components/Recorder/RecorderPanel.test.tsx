import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import i18n from '../../i18n'
import { useStore } from '../../store'
import { RecorderPanel } from './RecorderPanel'

const recorder = vi.hoisted(() => ({
  current: {
    state: 'idle' as string,
    blob: null as Blob | null,
    stream: null,
    duration: 0,
    error: null,
    start: vi.fn(),
    pause: vi.fn(),
    resume: vi.fn(),
    stop: vi.fn(),
    discard: vi.fn(),
  },
}))

vi.mock('./useMediaRecorder', () => ({
  useMediaRecorder: () => recorder.current,
  getFileExtension: () => 'webm',
  getPreferredMimeType: () => 'audio/webm',
}))

vi.mock('./RecordingSources', () => ({ RecordingSources: () => null }))
vi.mock('./AudioLevelMeter', () => ({ AudioLevelMeter: () => null }))

describe('RecorderPanel recording guard', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    useStore.getState().reset()
    recorder.current.state = 'recording'
    recorder.current.blob = null
    recorder.current.discard = vi.fn(() => {
      recorder.current.state = 'idle'
      recorder.current.blob = null
    })
  })

  it('marks a recording as at stake while recording, not after Discard, not after unmount', () => {
    const { rerender, unmount } = render(<RecorderPanel />)
    expect(useStore.getState().recordingActive).toBe(true)

    fireEvent.click(screen.getByRole('button', { name: 'Discard' }))
    rerender(<RecorderPanel />)
    expect(recorder.current.state).toBe('idle')
    expect(useStore.getState().recordingActive).toBe(false)

    recorder.current.state = 'paused'
    rerender(<RecorderPanel />)
    expect(useStore.getState().recordingActive).toBe(true)
    unmount()
    expect(useStore.getState().recordingActive).toBe(false)
  })
})
