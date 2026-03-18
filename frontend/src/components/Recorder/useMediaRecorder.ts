import { useState, useRef, useCallback, useEffect } from 'react'

export type RecorderState = 'idle' | 'recording' | 'paused' | 'stopped'

interface UseMediaRecorderOptions {
  audioDeviceId?: string
  videoDeviceId?: string
  useCamera?: boolean
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

  const stopAllTracks = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    setStream(null)
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      streamRef.current?.getTracks().forEach((t) => t.stop())
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
    setError(null)
    setBlob(null)
    chunksRef.current = []
    resetTimer()

    try {
      const constraints: MediaStreamConstraints = {
        audio: options.audioDeviceId
          ? { deviceId: { exact: options.audioDeviceId } }
          : true,
      }
      if (options.useCamera) {
        constraints.video = options.videoDeviceId
          ? { deviceId: { exact: options.videoDeviceId } }
          : true
      }

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = mediaStream
      setStream(mediaStream)

      const mimeType = getPreferredMimeType(!!options.useCamera)
      const recorder = new MediaRecorder(mediaStream, mimeType ? { mimeType } : undefined)

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
        pauseTimer()
      }

      recorder.onerror = () => {
        setError('deviceDisconnected')
        recorder.stop()
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
  }, [options.audioDeviceId, options.videoDeviceId, options.useCamera, resetTimer, startTimer, pauseTimer])

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
      stopAllTracks()
    }
  }, [stopAllTracks])

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
