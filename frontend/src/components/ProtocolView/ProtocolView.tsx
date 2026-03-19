import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { api } from '../../api/client'
import { ProtocolCard } from './ProtocolCard'
import { formatTime, downloadText } from '../../utils/format'
import type { ProtocolResult } from '../../api/types'

function protocolToText(protocol: ProtocolResult, t: (key: string) => string): string {
  let text = `${t('editor.protocol')}: ${protocol.title}\n`
  text += `${t('editor.participants')}: ${protocol.participants.join(', ')}\n`

  if (protocol.key_points.length > 0) {
    text += `\n${t('editor.keyPoints').toUpperCase()}\n`
    protocol.key_points.forEach((kp, i) => {
      const ts = kp.timestamp !== null ? `[${formatTime(kp.timestamp)}] ` : ''
      text += `${i + 1}. ${ts}${kp.speaker} — ${kp.topic}\n   ${kp.content}\n\n`
    })
  }

  if (protocol.decisions.length > 0) {
    text += `${t('editor.decisions').toUpperCase()}\n`
    protocol.decisions.forEach((d, i) => {
      const ts = d.timestamp !== null ? `[${formatTime(d.timestamp)}] ` : ''
      text += `${i + 1}. ${ts}${d.decision}\n\n`
    })
  }

  if (protocol.action_items.length > 0) {
    text += `${t('editor.actionItems').toUpperCase()}\n`
    protocol.action_items.forEach((ai, i) => {
      const ts = ai.timestamp !== null ? ` (${formatTime(ai.timestamp)})` : ''
      text += `${i + 1}. ${ai.assignee} — ${ai.task}${ts}\n\n`
    })
  }

  return text.trimEnd()
}

function protocolToMarkdown(protocol: ProtocolResult, t: (key: string) => string): string {
  let md = `# ${t('editor.protocol')}: ${protocol.title}\n\n`
  md += `**${t('editor.participants')}:** ${protocol.participants.join(', ')}\n`

  if (protocol.key_points.length > 0) {
    md += `\n## ${t('editor.keyPoints')}\n\n`
    protocol.key_points.forEach((kp, i) => {
      const ts = kp.timestamp !== null ? `[${formatTime(kp.timestamp)}] ` : ''
      md += `${i + 1}. **${ts}${kp.speaker}** — ${kp.topic}\n   ${kp.content}\n\n`
    })
  }

  if (protocol.decisions.length > 0) {
    md += `## ${t('editor.decisions')}\n\n`
    protocol.decisions.forEach((d, i) => {
      const ts = d.timestamp !== null ? `**[${formatTime(d.timestamp)}]** ` : ''
      md += `${i + 1}. ${ts}${d.decision}\n\n`
    })
  }

  if (protocol.action_items.length > 0) {
    md += `## ${t('editor.actionItems')}\n\n`
    protocol.action_items.forEach((ai) => {
      const ts = ai.timestamp !== null ? ` *(${formatTime(ai.timestamp)})*` : ''
      md += `- [ ] **${ai.assignee}** — ${ai.task}${ts}\n`
    })
  }

  return md.trimEnd()
}

export function ProtocolView() {
  const { t } = useTranslation()
  const transcriptionId = useStore((s) => s.transcriptionId)
  const protocol = useStore((s) => s.protocol)
  const setProtocol = useStore((s) => s.setProtocol)
  const file = useStore((s) => s.file)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const baseName = file?.original_filename?.replace(/\.[^.]+$/, '') || 'transcription'

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleGenerate = async () => {
    if (!transcriptionId) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.generateProtocol(transcriptionId)
      setProtocol(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Protocol generation failed')
    } finally {
      setLoading(false)
    }
  }

  if (!protocol && !loading) {
    return (
      <div className="p-6 text-center">
        <button
          onClick={handleGenerate}
          className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-500"
        >
          {t('editor.generateProtocol')} ✨
        </button>
        {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="p-6 text-center text-gray-400">
        <div className="animate-spin h-6 w-6 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
        {t('editor.generatingProtocol')}
      </div>
    )
  }

  if (!protocol) return null

  const copyIcon = (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
  )
  const checkIcon = (
    <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
  )
  const downloadIcon = (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
  )

  const btnCopy = "px-4 py-1.5 text-sm rounded flex items-center gap-2 text-gray-300 bg-gray-700 hover:bg-gray-600"
  const btnDownload = "px-4 py-1.5 text-sm rounded flex items-center gap-2 text-white bg-green-700 hover:bg-green-600"

  return (
    <div className="p-4 space-y-4">
      {/* Title & Participants */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <h2 className="text-base font-medium text-white mb-1">{protocol.title}</h2>
        <p className="text-xs text-gray-400">
          {t('editor.participants')}: {protocol.participants.join(', ')}
        </p>
      </div>

      {/* Key Points */}
      {protocol.key_points.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-gray-400 mb-2">{t('editor.keyPoints')}</h2>
          <div className="space-y-2">
            {protocol.key_points.map((kp, i) => (
              <ProtocolCard
                key={i}
                timestamp={kp.timestamp}
                label={`${kp.speaker} — ${kp.topic}`}
                description={kp.content}
              />
            ))}
          </div>
        </div>
      )}

      {/* Decisions */}
      {protocol.decisions.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-gray-400 mb-2">{t('editor.decisions')}</h2>
          <div className="space-y-2">
            {protocol.decisions.map((d, i) => (
              <ProtocolCard
                key={i}
                timestamp={d.timestamp}
                label={d.decision}
                description=""
              />
            ))}
          </div>
        </div>
      )}

      {/* Action Items */}
      {protocol.action_items.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-gray-400 mb-2">{t('editor.actionItems')}</h2>
          <div className="space-y-2">
            {protocol.action_items.map((ai, i) => (
              <ProtocolCard
                key={i}
                timestamp={ai.timestamp}
                label={ai.assignee}
                description={ai.task}
              />
            ))}
          </div>
        </div>
      )}

      {/* Copy & Download buttons */}
      <div className="flex justify-end gap-2 pt-3 border-t border-gray-700">
        <button onClick={() => handleCopy(protocolToText(protocol, t))} className={btnCopy}>
          {copied ? checkIcon : copyIcon}
          {copied ? t('editor.copied') : t('editor.copyProtocol')}
        </button>
        <button onClick={() => downloadText(protocolToText(protocol, t), `${baseName}_protocol.txt`)} className={btnDownload}>
          {downloadIcon}
          {t('editor.downloadProtocolTxt')}
        </button>
        <button onClick={() => downloadText(protocolToMarkdown(protocol, t), `${baseName}_protocol.md`)} className={btnDownload}>
          {downloadIcon}
          {t('editor.downloadProtocolMd')}
        </button>
      </div>
    </div>
  )
}
