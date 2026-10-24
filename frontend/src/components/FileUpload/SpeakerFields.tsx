import { useTranslation } from 'react-i18next'

interface SpeakerValues {
  detectSpeakers: boolean
  minSpeakers: number
  maxSpeakers: number
}

interface SpeakerFieldsProps extends SpeakerValues {
  onChange: (patch: Partial<SpeakerValues>) => void
  disabled?: boolean
}

export function SpeakerFields({
  detectSpeakers,
  minSpeakers,
  maxSpeakers,
  onChange,
  disabled = false,
}: SpeakerFieldsProps) {
  const { t } = useTranslation()
  return (
    <>
      <label className="flex items-center gap-2 py-1.5">
        <input
          type="checkbox"
          checked={detectSpeakers}
          disabled={disabled}
          onChange={(e) => onChange({ detectSpeakers: e.target.checked })}
          className="rounded shrink-0"
        />
        <span className="text-sm text-gray-300">{t('settings.detectSpeakers')}</span>
      </label>
      {detectSpeakers && (
        <>
          <div className="min-w-0">
            <label className="block text-xs text-gray-400 mb-1">{t('settings.minSpeakers')}</label>
            <input
              type="number"
              min={1}
              max={20}
              value={minSpeakers}
              disabled={disabled}
              onChange={(e) => {
                const val = Math.max(1, Math.min(20, Number(e.target.value)))
                onChange({
                  minSpeakers: val,
                  maxSpeakers: val > maxSpeakers ? val : maxSpeakers,
                })
              }}
              className="bg-gray-700 text-white text-sm rounded px-3 py-1.5 w-16"
            />
          </div>
          <div className="min-w-0">
            <label className="block text-xs text-gray-400 mb-1">{t('settings.maxSpeakers')}</label>
            <input
              type="number"
              min={1}
              max={20}
              value={maxSpeakers}
              disabled={disabled}
              onChange={(e) => {
                const val = Math.max(1, Math.min(20, Number(e.target.value)))
                onChange({
                  maxSpeakers: val,
                  minSpeakers: val < minSpeakers ? val : minSpeakers,
                })
              }}
              className="bg-gray-700 text-white text-sm rounded px-3 py-1.5 w-16"
            />
          </div>
        </>
      )}
    </>
  )
}
