import { useTranslation } from 'react-i18next'
import { useStore } from '../store'
import { LANGUAGES, LANGUAGES_WITH_AUTO } from '../utils/languages'

interface Props {
  value: string
  onChange: (value: string) => void
  includeAuto?: boolean
  className?: string
  disabled?: boolean
}

export function LanguageSelect({ value, onChange, includeAuto, className, disabled }: Props) {
  const { t } = useTranslation()
  const popularLanguages = useStore((s) => s.config?.popular_languages) || []

  const allCodes: readonly string[] = includeAuto ? LANGUAGES_WITH_AUTO : LANGUAGES
  const popular = popularLanguages.filter((code) => allCodes.includes(code))
  const rest = allCodes.filter((code) => code !== 'auto' && !popular.includes(code))

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={className}
      disabled={disabled}
    >
      {includeAuto && <option value="auto">{t('languages.auto')}</option>}
      {popular.length > 0 && (
        <>
          {popular.map((code) => (
            <option key={code} value={code}>{t(`languages.${code}`, code)}</option>
          ))}
          <option disabled>{'───────────'}</option>
        </>
      )}
      {rest.map((code) => (
        <option key={code} value={code}>{t(`languages.${code}`, code)}</option>
      ))}
    </select>
  )
}
