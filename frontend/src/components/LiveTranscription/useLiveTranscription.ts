import { useRef, useCallback, useEffect } from 'react'
import { useStore } from '../../store'
import { api } from '../../api/client'
import type { LiveMessage } from '../../api/types'

export function useLiveTranscription() {
  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const {
    liveSessionActive,
    setLiveSessionActive,
    setLiveTranscriptionId,
    setLiveLines,
    setLiveBufferText,
  } = useStore()

  const cleanup = useCallback(() => {
    setLiveSessionActive(false)
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {})
      audioContextRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [setLiveSessionActive])

  const start = useCallback(async (language?: string, deviceId?: string) => {
    try {
      // Get microphone stream
      const constraints: MediaStreamConstraints = {
        audio: deviceId ? { deviceId: { exact: deviceId } } : true,
      }
      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream

      // Set up AudioContext and worklet
      const audioContext = new AudioContext({ sampleRate: 48000 })
      audioContextRef.current = audioContext

      const base = import.meta.env.BASE_URL || '/'
      await audioContext.audioWorklet.addModule(`${base}audio-worklet-processor.js`)

      const source = audioContext.createMediaStreamSource(stream)
      sourceRef.current = source

      const workletNode = new AudioWorkletNode(audioContext, 'pcm-processor')
      source.connect(workletNode)
      workletNode.connect(audioContext.destination) // needed to keep processing

      // Open WebSocket
      const ws = api.connectLiveWebSocket(language)
      wsRef.current = ws

      ws.binaryType = 'arraybuffer'

      ws.onopen = () => {
        setLiveSessionActive(true)
      }

      // Forward PCM from worklet to WebSocket
      workletNode.port.onmessage = (event: MessageEvent) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(event.data)
        }
      }

      ws.onmessage = (event: MessageEvent) => {
        const msg: LiveMessage = JSON.parse(event.data)
        switch (msg.type) {
          case 'session_started':
            setLiveTranscriptionId(msg.transcription_id)
            break
          case 'transcription_update':
            setLiveLines(msg.lines)
            setLiveBufferText(msg.buffer_text)
            break
          case 'session_complete':
            setLiveTranscriptionId(msg.transcription_id)
            cleanup()
            break
          case 'error':
            console.error('Live transcription error:', msg.detail)
            cleanup()
            break
          case 'config':
            // Config received from WLK, no action needed
            break
        }
      }

      ws.onerror = () => {
        cleanup()
      }

      ws.onclose = () => {
        cleanup()
      }
    } catch (err) {
      console.error('Failed to start live transcription:', err)
      cleanup()
      throw err
    }
  }, [setLiveSessionActive, setLiveTranscriptionId, setLiveLines, setLiveBufferText, cleanup])

  const stop = useCallback(() => {
    // Send empty frame to signal end of audio
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(new ArrayBuffer(0))
    }
    // Stop audio capture
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => { cleanup() }
  }, [cleanup])

  return { isActive: liveSessionActive, start, stop }
}
