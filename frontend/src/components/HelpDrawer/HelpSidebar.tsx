import { useTranslation } from 'react-i18next'
import { sections } from './helpSections'
import type { HelpSectionId } from './helpSections'

interface HelpSidebarProps {
  activeId: HelpSectionId
  onSelect: (id: HelpSectionId) => void
}

export function HelpSidebar({ activeId, onSelect }: HelpSidebarProps) {
  const { t } = useTranslation()

  return (
    <nav
      aria-label={t('help.title')}
      className="w-[200px] shrink-0 border-r border-gray-700 overflow-y-auto py-4"
    >
      <ul className="space-y-1">
        {sections.map((section) => {
          const isActive = section.id === activeId
          return (
            <li key={section.id}>
              <button
                type="button"
                onClick={() => onSelect(section.id)}
                className={`w-full text-left px-4 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 ${
                  isActive
                    ? 'bg-gray-800 text-white border-l-2 border-blue-500'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50 border-l-2 border-transparent'
                }`}
              >
                {t(`help.sections.${section.id}`)}
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
