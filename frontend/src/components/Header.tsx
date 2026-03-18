import { useTranslation } from 'react-i18next'
import { useStore } from '../store'

export function Header() {
  const { t, i18n } = useTranslation()
  const config = useStore((s) => s.config)

  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === 'de' ? 'en' : 'de')
  }

  return (
    <header className="flex items-center justify-between px-6 py-3 bg-gray-900 border-b border-gray-700">
      <h1 className="text-lg font-semibold text-white">{t('title')}</h1>
      <div className="flex items-center gap-4">
        <button onClick={toggleLanguage} className="text-sm text-gray-300 hover:text-white">
          {i18n.language === 'de' ? 'EN' : 'DE'} | {i18n.language.toUpperCase()}
        </button>
        {config?.logout_url && (
          <a href={config.logout_url} className="text-sm text-red-400 hover:text-red-300">
            {t('common.logout')}
          </a>
        )}
      </div>
    </header>
  )
}
