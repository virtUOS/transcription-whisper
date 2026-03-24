import { useEffect, useRef, useState } from 'react'
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
  const doneRef = useRef(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!transcriptionId || status === 'completed' || status === 'failed') return

    doneRef.current = false
    retriesRef.current = 0

    const markDone = () => {
      doneRef.current = true
      wsRef.current?.close()
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }

    const handleCompleted = async () => {
      markDone()
      setStatus('completed')
      const result = await api.getTranscription(transcriptionId)
      setResult(result)
    }

    const handleFailed = (error?: string) => {
      markDone()
      setStatus('failed')
      if (error) setErrorMessage(error)
    }

    const connect = () => {
      if (doneRef.current) return
      const ws = api.connectWebSocket(transcriptionId)
      wsRef.current = ws

      ws.onmessage = (event) => {
        if (doneRef.current) return
        const data = JSON.parse(event.data)
        if (data.type === 'status') {
          if (data.status === 'completed') {
            handleCompleted()
          } else if (data.status === 'failed') {
            handleFailed(data.error)
          } else {
            setStatus(data.status)
          }
        }
      }

      ws.onclose = () => {
        if (doneRef.current) return
        if (retriesRef.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, retriesRef.current), 30000)
          retriesRef.current++
          setTimeout(connect, delay)
        } else {
          // Fall back to HTTP polling
          pollRef.current = setInterval(async () => {
            if (doneRef.current) return
            try {
              const s = await api.getStatus(transcriptionId)
              if (s.status === 'completed') {
                handleCompleted()
              } else if (s.status === 'failed') {
                handleFailed(s.error || undefined)
              }
            } catch { /* ignore */ }
          }, 10000)
        }
      }
    }

    connect()
    return () => {
      doneRef.current = true
      wsRef.current?.close()
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [transcriptionId, status, setStatus, setResult])

  if (!transcriptionId || status === 'completed') return null

  if (status === 'failed') {
    return (
      <div className="mx-6 my-4 p-4 bg-red-900/30 rounded-lg border border-red-700">
        <div className="flex items-center gap-3">
          <span className="text-red-400 text-lg">!</span>
          <div>
            <span className="text-red-300 text-sm">{t('transcription.failed')}</span>
            {errorMessage && <p className="text-red-400/80 text-xs mt-1">{errorMessage}</p>}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-6 my-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
      <div className="flex items-center gap-3">
        <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
        <span className="text-gray-300 text-sm">{t('transcription.inProgress')}</span>
      </div>
    </div>
  )
}
