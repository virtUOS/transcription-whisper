import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../store'

export function Header() {
  const { t, i18n } = useTranslation()
  const config = useStore((s) => s.config)
  const [burgerOpen, setBurgerOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === 'de' ? 'en' : 'de')
  }

  const openHelp = () => {
    useStore.getState().setHelpOpen(true)
    setBurgerOpen(false)
  }

  const openPresets = () => {
    const state = useStore.getState()
    if (!state.confirmLeaveUpload(t('upload.confirmLeave'))) return
    state.setCurrentView('presets')
    setBurgerOpen(false)
  }

  const handleToggleLanguage = () => {
    toggleLanguage()
    setBurgerOpen(false)
  }

  const handleLogout = () => {
    if (!useStore.getState().confirmLeaveUpload(t('upload.confirmLeave'))) return
    if (config?.logout_url) {
      window.location.href = config.logout_url
    }
  }

  useEffect(() => {
    if (!burgerOpen) return
    const onMouseDown = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setBurgerOpen(false)
      }
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setBurgerOpen(false)
    }
    document.addEventListener('mousedown', onMouseDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onMouseDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [burgerOpen])

  const buttonClass = 'text-sm text-gray-300 hover:text-white focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500'
  const logoutButtonClass = 'text-sm text-red-400 hover:text-red-300 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500'

  return (
    <header className="relative flex items-center justify-between gap-2 px-6 py-3 bg-gray-900 border-b border-gray-700">
      <div className="flex items-center gap-3 min-w-0">
        <img src={`${import.meta.env.BASE_URL}whisper-logo.svg`} alt="Transcription Service" className="h-8 w-8 shrink-0" />
        <h1 className="text-lg font-semibold text-white truncate">{t('title')}</h1>
      </div>

      {/* Desktop: inline button row */}
      <div className="hidden md:flex items-center gap-4">
        <button
          type="button"
          onClick={openHelp}
          aria-label={t('help.open')}
          title={t('help.open')}
          className={buttonClass}
        >
          ?
        </button>
        <button onClick={openPresets} className={buttonClass}>
          {t('nav.presets')}
        </button>
        <button
          onClick={handleToggleLanguage}
          className={buttonClass}
          title={i18n.language === 'de' ? 'Switch to English' : 'Auf Deutsch wechseln'}
          aria-label={i18n.language === 'de' ? 'Switch to English' : 'Auf Deutsch wechseln'}
        >
          {(i18n.language === 'de' ? 'en' : 'de').toUpperCase()}
        </button>
        {config?.logout_url && (
          <button onClick={handleLogout} className={logoutButtonClass}>
            {t('common.logout')}
          </button>
        )}
      </div>

      {/* Mobile: burger trigger + dropdown */}
      <div className="md:hidden" ref={containerRef}>
        <button
          type="button"
          onClick={() => setBurgerOpen((open) => !open)}
          aria-label={t('nav.menu')}
          aria-expanded={burgerOpen}
          aria-haspopup="menu"
          aria-controls="header-mobile-menu"
          className={buttonClass}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        {burgerOpen && (
          <div
            id="header-mobile-menu"
            role="menu"
            className="absolute right-0 top-full mt-1 w-48 bg-gray-900 border border-gray-700 rounded-md shadow-lg z-40 flex flex-col py-2"
          >
            <button
              type="button"
              role="menuitem"
              onClick={openHelp}
              className={`${buttonClass} text-left px-4 py-2`}
            >
              {t('help.open')}
            </button>
            <button
              type="button"
              role="menuitem"
              onClick={openPresets}
              className={`${buttonClass} text-left px-4 py-2`}
            >
              {t('nav.presets')}
            </button>
            <button
              type="button"
              role="menuitem"
              onClick={handleToggleLanguage}
              className={`${buttonClass} text-left px-4 py-2`}
            >
              {i18n.language === 'de' ? 'Switch to English' : 'Auf Deutsch wechseln'}
            </button>
            {config?.logout_url && (
              <button
                type="button"
                role="menuitem"
                onClick={() => { setBurgerOpen(false); handleLogout() }}
                className={`${logoutButtonClass} text-left px-4 py-2`}
              >
                {t('common.logout')}
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  )
}
