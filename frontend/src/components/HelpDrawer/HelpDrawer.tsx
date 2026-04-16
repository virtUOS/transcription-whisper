import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { HelpSidebar } from './HelpSidebar'
import { HelpContent } from './HelpContent'
import { sections, viewToSection } from './helpSections'
import type { HelpSectionId } from './helpSections'

type AppView = 'archive' | 'upload' | 'record' | 'detail' | 'presets'

export function HelpDrawer() {
  const { t } = useTranslation()
  const open = useStore((s) => s.helpOpen)
  const initialSection = useStore((s) => s.helpInitialSection)
  const closeHelp = useStore((s) => s.closeHelp)
  const currentView = useStore((s) => s.currentView) as AppView

  // Compute the section to land on when opening.
  // Because the component unmounts when !open, useState(derivedSection) will
  // always receive the correct value on the next mount.
  const derivedSection = useMemo<HelpSectionId>(() => {
    if (initialSection && sections.some((s) => s.id === initialSection)) {
      return initialSection as HelpSectionId
    }
    return viewToSection[currentView] ?? 'getting-started'
  }, [initialSection, currentView])

  const [activeId, setActiveId] = useState<HelpSectionId>(derivedSection)
  const drawerRef = useRef<HTMLDivElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)

  // Focus management: trap focus inside the drawer and restore on close.
  useEffect(() => {
    if (open) {
      previousFocusRef.current = document.activeElement as HTMLElement | null
      // Defer focus to next frame so the drawer is mounted.
      requestAnimationFrame(() => {
        closeButtonRef.current?.focus()
      })
    } else if (previousFocusRef.current) {
      previousFocusRef.current.focus()
      previousFocusRef.current = null
    }
  }, [open])

  // Keyboard handling: Escape closes, Tab stays trapped inside the drawer.
  useEffect(() => {
    if (!open) return
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        closeHelp()
        return
      }
      if (e.key !== 'Tab' || !drawerRef.current) return
      const focusables = drawerRef.current.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      if (focusables.length === 0) return
      const first = focusables[0]
      const last = focusables[focusables.length - 1]
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [open, closeHelp])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end"
      role="dialog"
      aria-modal="true"
      aria-labelledby="help-drawer-title"
    >
      <button
        type="button"
        aria-label={t('help.close')}
        onClick={closeHelp}
        className="absolute inset-0 bg-black/50 cursor-default"
        tabIndex={-1}
      />
      <div
        ref={drawerRef}
        className="relative flex flex-col bg-gray-900 border-l border-gray-700 w-full md:w-[35vw] md:min-w-[420px] max-w-[720px] shadow-2xl"
      >
        <div className="flex items-center justify-between px-6 py-3 border-b border-gray-700">
          <h2 id="help-drawer-title" className="text-lg font-semibold text-white">
            {t('help.title')}
          </h2>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={closeHelp}
            aria-label={t('help.close')}
            className="text-gray-400 hover:text-white text-xl leading-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 rounded"
          >
            ✕
          </button>
        </div>
        <div className="flex flex-1 min-h-0">
          <HelpSidebar activeId={activeId} onSelect={setActiveId} />
          <HelpContent sectionId={activeId} />
        </div>
      </div>
    </div>
  )
}

export default HelpDrawer
