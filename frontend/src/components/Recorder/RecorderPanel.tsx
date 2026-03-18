import { useTranslation } from 'react-i18next'

export function RecorderPanel() {
  const { t } = useTranslation()
  return (
    <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center text-gray-400">
      {t('recorder.startRecording')}
    </div>
  )
}
