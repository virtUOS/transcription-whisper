import { useTranslation } from 'react-i18next'
import { useStore } from '../store'

export function Header() {
  const { t, i18n } = useTranslation()
  const config = useStore((s) => s.config)

  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === 'de' ? 'en' : 'de')
  }

  return (
    <header className="flex flex-wrap items-center justify-between gap-2 px-6 py-3 bg-gray-900 border-b border-gray-700">
      <div className="flex items-center gap-3 min-w-0">
        <img src={`${import.meta.env.BASE_URL}whisper-logo.svg`} alt="Transcription Service" className="h-8 w-8 shrink-0" />
        <h1 className="text-lg font-semibold text-white truncate">{t('title')}</h1>
      </div>
      <div className="flex flex-wrap items-center gap-4">
        <button
          onClick={() => useStore.getState().setCurrentView('presets')}
          className="text-sm text-gray-300 hover:text-white"
        >
          {t('nav.presets')}
        </button>
        <button
          onClick={toggleLanguage}
          className="text-sm text-gray-300 hover:text-white"
          title={i18n.language === 'de' ? 'Switch to English' : 'Auf Deutsch wechseln'}
          aria-label={i18n.language === 'de' ? 'Switch to English' : 'Auf Deutsch wechseln'}
        >
          {(i18n.language === 'de' ? 'en' : 'de').toUpperCase()}
        </button>
        {config?.logout_url && (
          <button
            onClick={() => { window.location.href = config.logout_url }}
            className="text-sm text-red-400 hover:text-red-300"
          >
            {t('common.logout')}
          </button>
        )}
      </div>
    </header>
  )
}
