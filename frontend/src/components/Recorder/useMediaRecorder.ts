import { useState, useRef, useCallback, useEffect } from 'react'

export type RecorderState = 'idle' | 'recording' | 'paused' | 'stopped'

interface UseMediaRecorderOptions {
  audioDeviceId?: string
  videoDeviceId?: string
  useCamera?: boolean
  captureSystemAudio?: boolean
}

interface UseMediaRecorderReturn {
  state: RecorderState
  blob: Blob | null
  stream: MediaStream | null
  duration: number
  error: string | null
  start: () => Promise<void>
  pause: () => void
  resume: () => void
  stop: () => void
  discard: () => void
}

function getPreferredMimeType(hasVideo: boolean): string {
  const candidates = hasVideo
    ? ['video/webm;codecs=vp9,opus', 'video/webm', 'video/mp4']
    : ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4']
  return candidates.find((t) => MediaRecorder.isTypeSupported(t)) || ''
}

function getFileExtension(mimeType: string): string {
  if (mimeType.includes('webm')) return 'webm'
  if (mimeType.includes('mp4')) return 'mp4'
  return 'webm'
}

export function useMediaRecorder(options: UseMediaRecorderOptions = {}): UseMediaRecorderReturn {
  const [state, setState] = useState<RecorderState>('idle')
  const [blob, setBlob] = useState<Blob | null>(null)
  const [duration, setDuration] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)

  const recorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const startTimeRef = useRef(0)
  const elapsedBeforePauseRef = useRef(0)
  const discardingRef = useRef(false)

  const displayStreamRef = useRef<MediaStream | null>(null)
  const mixAudioContextRef = useRef<AudioContext | null>(null)
  const displayEndedHandlerRef = useRef<(() => void) | null>(null)

  const stopAllTracks = useCallback(() => {
    // Remove ended listener before stopping tracks
    if (displayEndedHandlerRef.current && displayStreamRef.current) {
      const track = displayStreamRef.current.getAudioTracks()[0]
      if (track) track.removeEventListener('ended', displayEndedHandlerRef.current)
      displayEndedHandlerRef.current = null
    }
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    displayStreamRef.current?.getTracks().forEach((t) => t.stop())
    displayStreamRef.current = null
    if (mixAudioContextRef.current) {
      mixAudioContextRef.current.close()
      mixAudioContextRef.current = null
    }
    setStream(null)
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      discardingRef.current = true
      if (recorderRef.current && recorderRef.current.state !== 'inactive') {
        recorderRef.current.stop()
      }
      if (timerRef.current) clearInterval(timerRef.current)
      streamRef.current?.getTracks().forEach((t) => t.stop())
      if (displayEndedHandlerRef.current && displayStreamRef.current) {
        const track = displayStreamRef.current.getAudioTracks()[0]
        if (track) track.removeEventListener('ended', displayEndedHandlerRef.current)
      }
      displayStreamRef.current?.getTracks().forEach((t) => t.stop())
      if (mixAudioContextRef.current) mixAudioContextRef.current.close()
    }
  }, [])

  const startTimer = useCallback(() => {
    startTimeRef.current = Date.now()
    timerRef.current = setInterval(() => {
      setDuration(elapsedBeforePauseRef.current + (Date.now() - startTimeRef.current))
    }, 200)
  }, [])

  const pauseTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    elapsedBeforePauseRef.current += Date.now() - startTimeRef.current
  }, [])

  const resetTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = null
    startTimeRef.current = 0
    elapsedBeforePauseRef.current = 0
    setDuration(0)
  }, [])

  const start = useCallback(async () => {
    if (recorderRef.current && recorderRef.current.state !== 'inactive') return
    setError(null)
    setBlob(null)
    chunksRef.current = []
    resetTimer()

    try {
      // Step 1: Get microphone stream
      const constraints: MediaStreamConstraints = {
        audio: options.audioDeviceId
          ? { deviceId: { exact: options.audioDeviceId } }
          : true,
      }
      if (options.useCamera && !options.captureSystemAudio) {
        constraints.video = options.videoDeviceId
          ? { deviceId: { exact: options.videoDeviceId } }
          : true
      }

      const micStream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = micStream

      let recordingStream: MediaStream = micStream

      // Step 2: If system audio, get display stream and mix
      if (options.captureSystemAudio) {
        let displayStream: MediaStream
        try {
          displayStream = await navigator.mediaDevices.getDisplayMedia({
            audio: true,
            video: true, // video: false throws TypeError in Chrome
          })
        } catch {
          // User cancelled picker or browser doesn't support it
          micStream.getTracks().forEach((t) => t.stop())
          streamRef.current = null
          setError('systemAudioFailed')
          return
        }

        // Stop the video track immediately — we only need audio
        displayStream.getVideoTracks().forEach((t) => t.stop())

        // Validate that display stream has audio
        if (displayStream.getAudioTracks().length === 0) {
          displayStream.getTracks().forEach((t) => t.stop())
          micStream.getTracks().forEach((t) => t.stop())
          streamRef.current = null
          setError('systemAudioFailed')
          return
        }

        displayStreamRef.current = displayStream

        // Listen for user clicking "Stop sharing" in browser UI
        const displayAudioTrack = displayStream.getAudioTracks()[0]
        const onDisplayEnded = () => {
          if (recorderRef.current && recorderRef.current.state !== 'inactive') {
            recorderRef.current.stop()
          }
        }
        displayAudioTrack.addEventListener('ended', onDisplayEnded)
        displayEndedHandlerRef.current = onDisplayEnded

        // Mix both streams via Web Audio API
        const audioCtx = new AudioContext()
        const micSource = audioCtx.createMediaStreamSource(micStream)
        const displaySource = audioCtx.createMediaStreamSource(displayStream)
        const destination = audioCtx.createMediaStreamDestination()
        micSource.connect(destination)
        displaySource.connect(destination)

        mixAudioContextRef.current = audioCtx
        recordingStream = destination.stream
      }

      setStream(recordingStream)

      const mimeType = getPreferredMimeType(!!options.useCamera && !options.captureSystemAudio)
      const recorder = new MediaRecorder(recordingStream, mimeType ? { mimeType } : undefined)

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = () => {
        // Skip blob creation if we're discarding
        if (discardingRef.current) {
          discardingRef.current = false
          return
        }
        const finalMime = recorder.mimeType || mimeType
        const recordedBlob = new Blob(chunksRef.current, { type: finalMime })
        setBlob(recordedBlob)
        setState('stopped')
        if (timerRef.current) pauseTimer()
        // Stop tracks after blob is created so MediaRecorder gets all data
        stopAllTracks()
      }

      recorder.onerror = () => {
        // Let onstop create blob from partial chunks so user can save their recording
        setError('deviceDisconnected')
        if (recorderRef.current?.state !== 'inactive') recorderRef.current?.stop()
        stopAllTracks()
      }

      recorderRef.current = recorder
      recorder.start(1000) // collect chunks every second
      setState('recording')
      startTimer()
    } catch (err) {
      if (options.useCamera && err instanceof DOMException && err.name === 'NotAllowedError') {
        setError('cameraFailed')
      } else {
        setError('micRequired')
      }
    }
  }, [options.audioDeviceId, options.videoDeviceId, options.useCamera, options.captureSystemAudio, resetTimer, startTimer, pauseTimer, stopAllTracks])

  const pause = useCallback(() => {
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.pause()
      setState('paused')
      pauseTimer()
    }
  }, [pauseTimer])

  const resume = useCallback(() => {
    if (recorderRef.current?.state === 'paused') {
      recorderRef.current.resume()
      setState('recording')
      startTimer()
    }
  }, [startTimer])

  const stop = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop()
      // Don't stopAllTracks() here — let onstop fire first to create the blob
    }
  }, [])

  const discard = useCallback(() => {
    discardingRef.current = true
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop()
    }
    stopAllTracks()
    setBlob(null)
    chunksRef.current = []
    resetTimer()
    setState('idle')
    setError(null)
  }, [stopAllTracks, resetTimer])

  return { state, blob, stream, duration, error, start, pause, resume, stop, discard }
}

export { getFileExtension, getPreferredMimeType }
