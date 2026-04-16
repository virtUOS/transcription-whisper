import { useEffect, useId } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../store'
import { LANGUAGES, LANGUAGES_WITH_AUTO, filterEnabledLanguages } from '../utils/languages'

interface Props {
  value: string
  onChange: (value: string) => void
  includeAuto?: boolean
  className?: string
  disabled?: boolean
  id?: string
}

export function LanguageSelect({ value, onChange, includeAuto, className, disabled, id }: Props) {
  const { t } = useTranslation()
  const popularLanguages = useStore((s) => s.config?.popular_languages) || []
  const enabledLanguages = useStore((s) => s.config?.enabled_languages) || []
  const autoId = useId()
  const effectiveId = id ?? autoId

  const baseList: readonly string[] = includeAuto ? LANGUAGES_WITH_AUTO : LANGUAGES
  const allCodes = filterEnabledLanguages(baseList, enabledLanguages)
  const popular = popularLanguages.filter((code) => allCodes.includes(code))
  const rest = allCodes.filter((code) => code !== 'auto' && !popular.includes(code))
  const userVisibleCount = allCodes.filter((code) => code !== 'auto').length
  const collapsedOnly = userVisibleCount === 1 && !includeAuto ? allCodes[0] : null

  useEffect(() => {
    if (collapsedOnly && value !== collapsedOnly) {
      onChange(collapsedOnly)
    }
  }, [collapsedOnly, value, onChange])

  if (collapsedOnly) {
    return (
      <output id={effectiveId} className={className ? `block ${className}` : 'block'}>
        {t(`languages.${collapsedOnly}`, collapsedOnly)}
      </output>
    )
  }

  return (
    <select
      id={effectiveId}
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
          {rest.length > 0 && <option disabled>{'───────────'}</option>}
        </>
      )}
      {rest.map((code) => (
        <option key={code} value={code}>{t(`languages.${code}`, code)}</option>
      ))}
    </select>
  )
}
