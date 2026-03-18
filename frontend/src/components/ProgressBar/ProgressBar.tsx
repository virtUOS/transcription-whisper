import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'

export function ProgressBar() {
  const { t } = useTranslation()
  const transcriptionId = useStore((s) => s.transcriptionId)
  const status = useStore((s) => s.transcriptionStatus)
  const setStatus = useStore((s) => s.setTranscriptionStatus)
  const setResult = useStore((s) => s.setTranscriptionResult)
  const wsRef = useRef<WebSocket | null>(null)
  const retriesRef = useRef(0)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!transcriptionId || status === 'completed' || status === 'failed') return

    const connect = () => {
      const ws = api.connectWebSocket(transcriptionId)
      wsRef.current = ws

      ws.onmessage = async (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'status') {
          setStatus(data.status)
          if (data.status === 'completed') {
            const result = await api.getTranscription(transcriptionId)
            setResult(result)
          }
        }
      }

      ws.onclose = () => {
        if (status !== 'completed' && status !== 'failed' && retriesRef.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, retriesRef.current), 30000)
          retriesRef.current++
          setTimeout(connect, delay)
        } else if (retriesRef.current >= 5) {
          pollRef.current = setInterval(async () => {
            try {
              const s = await api.getStatus(transcriptionId)
              setStatus(s.status)
              if (s.status === 'completed') {
                clearInterval(pollRef.current!)
                pollRef.current = null
                const result = await api.getTranscription(transcriptionId)
                setResult(result)
              } else if (s.status === 'failed') {
                clearInterval(pollRef.current!)
                pollRef.current = null
              }
            } catch { /* ignore */ }
          }, 10000)
        }
      }
    }

    connect()
    return () => {
      wsRef.current?.close()
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [transcriptionId, status, setStatus, setResult])

  if (!transcriptionId || status === 'completed') return null

  return (
    <div className="mx-6 my-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
      <div className="flex items-center gap-3">
        <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
        <span className="text-gray-300 text-sm">
          {status === 'failed' ? t('transcription.failed') : t('transcription.inProgress')}
        </span>
      </div>
    </div>
  )
}
