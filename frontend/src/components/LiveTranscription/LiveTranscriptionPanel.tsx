import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { useLiveTranscription } from './useLiveTranscription'
import LiveTranscript from './LiveTranscript'

export default function LiveTranscriptionPanel() {
  const { t } = useTranslation()
  const { isActive, start, stop } = useLiveTranscription()
  const {
    liveLines,
    liveBufferText,
    liveTranscriptionId,
    setCurrentView,
    setTranscriptionId,
    setTranscriptionStatus,
    setTranscriptionResult,
    setFile,
    setSpeakerMappings,
  } = useStore()

  const [language, setLanguage] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [finishing, setFinishing] = useState(false)

  const languages = [
    { code: '', label: t('live.autoDetect') },
    { code: 'en', label: 'English' },
    { code: 'de', label: 'Deutsch' },
    { code: 'es', label: 'Español' },
    { code: 'fr', label: 'Français' },
    { code: 'it', label: 'Italiano' },
    { code: 'pt', label: 'Português' },
    { code: 'nl', label: 'Nederlands' },
    { code: 'ja', label: '日本語' },
    { code: 'zh', label: '中文' },
    { code: 'ko', label: '한국어' },
    { code: 'ru', label: 'Русский' },
    { code: 'ar', label: 'العربية' },
  ]

  const handleStart = useCallback(async () => {
    setError(null)
    try {
      await start(language || undefined)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('live.errorStarting'))
    }
  }, [start, language, t])

  const handleStop = useCallback(() => {
    setFinishing(true)
    stop()
  }, [stop])

  // When session completes and we have a transcription ID, navigate to detail
  const handleViewResult = useCallback(async () => {
    if (!liveTranscriptionId) return
    try {
      const result = await api.getTranscription(liveTranscriptionId)
      setTranscriptionId(liveTranscriptionId)
      setTranscriptionStatus('completed')
      setTranscriptionResult(result)
      setSpeakerMappings(result.speaker_mappings || {})
      // Use the file info from the transcription list to set file
      const list = await api.listTranscriptions()
      const item = list.find(i => i.id === liveTranscriptionId)
      if (item) {
        const ext = item.original_filename.split('.').pop()?.toLowerCase() || ''
        setFile({ id: item.file_id, original_filename: item.original_filename, media_type: ext, file_size: item.file_size })
      }
      setCurrentView('detail')
    } catch (err) {
      console.error('Failed to load transcription:', err)
    }
  }, [liveTranscriptionId, setTranscriptionId, setTranscriptionStatus, setTranscriptionResult, setFile, setSpeakerMappings, setCurrentView])

  const sessionComplete = !isActive && liveTranscriptionId && liveLines.length > 0

  return (
    <div className="flex flex-col gap-4 h-full">
      <h2 className="text-xl font-semibold text-gray-100">{t('live.title')}</h2>

      {!isActive && !sessionComplete && (
        <div className="flex flex-col gap-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">{t('live.language')}</label>
            <select
              value={language}
              onChange={e => setLanguage(e.target.value)}
              className="w-full rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-gray-200 text-sm"
            >
              {languages.map(l => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleStart}
            className="rounded-lg bg-red-600 hover:bg-red-500 px-6 py-3 text-white font-medium transition-colors"
          >
            {t('live.start')}
          </button>
          {error && (
            <p className="text-red-400 text-sm">{error}</p>
          )}
        </div>
      )}

      {isActive && (
        <div className="flex flex-col gap-3 flex-1">
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-2 text-sm text-red-400">
              <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
              {t('live.recording')}
            </span>
          </div>
          <LiveTranscript lines={liveLines} bufferText={liveBufferText} />
          <button
            onClick={handleStop}
            disabled={finishing}
            className="rounded-lg bg-gray-700 hover:bg-gray-600 px-6 py-3 text-white font-medium transition-colors disabled:opacity-50"
          >
            {finishing ? t('live.finishing') : t('live.stop')}
          </button>
        </div>
      )}

      {sessionComplete && (
        <div className="flex flex-col gap-3">
          <p className="text-green-400 text-sm">{t('live.sessionComplete')}</p>
          <LiveTranscript lines={liveLines} bufferText="" />
          <button
            onClick={handleViewResult}
            className="rounded-lg bg-blue-600 hover:bg-blue-500 px-6 py-3 text-white font-medium transition-colors"
          >
            {t('live.viewResult')}
          </button>
        </div>
      )}
    </div>
  )
}
