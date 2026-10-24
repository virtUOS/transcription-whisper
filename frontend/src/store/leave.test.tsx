import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, cleanup } from '@testing-library/react'
import { useStore } from './index'
import { useBeforeUnloadWarning } from '../hooks/useBeforeUnloadWarning'

const messages = { upload: 'upload msg', recording: 'recording msg', unsavedEdits: 'edits msg' }

function Probe() {
  useBeforeUnloadWarning()
  return null
}

describe('confirmLeave', () => {
  let confirmSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    useStore.getState().reset()
    confirmSpy = vi.spyOn(window, 'confirm')
  })
  afterEach(() => {
    confirmSpy.mockRestore()
  })

  it('returns true without asking when nothing is at stake', () => {
    expect(useStore.getState().confirmLeave(messages)).toBe(true)
    expect(confirmSpy).not.toHaveBeenCalled()
  })

  it('asks with the recording message while a recording is active and clears the flag on confirm', () => {
    confirmSpy.mockReturnValue(true)
    useStore.getState().setRecordingActive(true)
    expect(useStore.getState().confirmLeave(messages)).toBe(true)
    expect(confirmSpy).toHaveBeenCalledWith('recording msg')
    expect(useStore.getState().recordingActive).toBe(false)
  })

  it('keeps the recording flag when the user declines', () => {
    confirmSpy.mockReturnValue(false)
    useStore.getState().setRecordingActive(true)
    expect(useStore.getState().confirmLeave(messages)).toBe(false)
    expect(useStore.getState().recordingActive).toBe(true)
  })

  it('keeps a running upload when the user declines', () => {
    confirmSpy.mockReturnValue(false)
    const controller = new AbortController()
    useStore.getState().setUploading(true)
    useStore.getState().setUploadAbortController(controller)
    expect(useStore.getState().confirmLeave(messages)).toBe(false)
    expect(controller.signal.aborted).toBe(false)
    expect(useStore.getState().uploading).toBe(true)
  })

  it('aborts the running upload on confirm', () => {
    confirmSpy.mockReturnValue(true)
    const controller = new AbortController()
    useStore.getState().setUploading(true)
    useStore.getState().setUploadAbortController(controller)
    expect(useStore.getState().confirmLeave(messages)).toBe(true)
    expect(confirmSpy).toHaveBeenCalledWith('upload msg')
    expect(controller.signal.aborted).toBe(true)
    expect(useStore.getState().uploading).toBe(false)
  })

  it('upload wins over recording', () => {
    useStore.getState().setUploading(true)
    useStore.getState().setRecordingActive(true)
    expect(useStore.getState().leaveReason()).toBe('upload')
  })

  it('reset clears the recording flag', () => {
    useStore.getState().setRecordingActive(true)
    useStore.getState().reset()
    expect(useStore.getState().leaveReason()).toBeNull()
  })

  it('asks with the editor message for unsaved edits in the detail view', () => {
    confirmSpy.mockReturnValue(true)
    useStore.getState().setCurrentView('detail')
    useStore.getState().setUnsavedEdits(true)
    expect(useStore.getState().confirmLeave(messages)).toBe(true)
    expect(confirmSpy).toHaveBeenCalledWith('edits msg')
    expect(useStore.getState().unsavedEdits).toBe(true)
  })

  it('does not ask for unsaved edits outside the detail view', () => {
    useStore.getState().setCurrentView('archive')
    useStore.getState().setUnsavedEdits(true)
    expect(useStore.getState().confirmLeave(messages)).toBe(true)
    expect(confirmSpy).not.toHaveBeenCalled()
  })

  it('lets upload and recording win over unsaved edits', () => {
    useStore.getState().setCurrentView('detail')
    useStore.getState().setUnsavedEdits(true)
    useStore.getState().setRecordingActive(true)
    expect(useStore.getState().leaveReason()).toBe('recording')
  })

  it('beforeunload is armed while the editor has unsaved edits', () => {
    useStore.getState().setCurrentView('detail')
    useStore.getState().setUnsavedEdits(true)
    render(<Probe />)
    const event = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(event)
    expect(event.defaultPrevented).toBe(true)
    cleanup()
  })

  it('beforeunload is not armed without unsaved edits', () => {
    render(<Probe />)
    const event = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(event)
    expect(event.defaultPrevented).toBe(false)
    cleanup()
  })

  it('still reports a recording after upload while no transcription was started', () => {
    useStore.setState({
      currentView: 'record',
      file: { id: 'f1', original_filename: 'r.webm', file_size: 1 } as never,
    })
    expect(useStore.getState().leaveReason()).toBe('recording')
    useStore.setState({ transcriptionId: 't1' })
    expect(useStore.getState().leaveReason()).toBeNull()
  })

  it('does not report an uploaded file in the upload view', () => {
    useStore.setState({
      currentView: 'upload',
      file: { id: 'f1', original_filename: 'a.mp3', file_size: 1 } as never,
    })
    expect(useStore.getState().leaveReason()).toBeNull()
  })
})
