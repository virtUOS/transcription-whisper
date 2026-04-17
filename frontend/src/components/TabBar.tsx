import { useTranslation } from 'react-i18next'
import { useStore } from '../store'

interface Props {
  onSpeakerNamesClick: () => void
}

export function TabBar({ onSpeakerNamesClick }: Props) {
  const { t } = useTranslation()
  const activeTab = useStore((s) => s.activeTab)
  const setActiveTab = useStore((s) => s.setActiveTab)
  const config = useStore((s) => s.config)

  const tabs = [
    { id: 'subtitles', label: t('editor.subtitles') },
    ...(config?.llm_available ? [{ id: 'analysis', label: t('editor.analysis') }] : []),
    { id: 'srt', label: 'SRT' },
    { id: 'vtt', label: 'VTT' },
    { id: 'json', label: 'JSON' },
    { id: 'txt', label: 'TXT' },
  ]

  return (
    <div className="flex items-center gap-1 px-6 py-2 bg-gray-800 border-b border-gray-700 overflow-x-auto [mask-image:linear-gradient(to_right,transparent,black_1rem,black_calc(100%-1rem),transparent)] sm:[mask-image:none]">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          className={`px-3 py-1 text-sm rounded ${
            activeTab === tab.id
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-700'
          }`}
        >
          {tab.label}
        </button>
      ))}
      <div className="ml-auto flex gap-2">
        <button onClick={onSpeakerNamesClick} className="px-3 py-1 text-sm text-gray-400 hover:text-white hover:bg-gray-700 rounded">
          {t('editor.speakerNames')}
        </button>
      </div>
    </div>
  )
}
