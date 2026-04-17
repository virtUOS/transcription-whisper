import { useEffect, useId } from 'react'
import { useTranslation } from 'react-i18next'
import { useStore } from '../store'
import { LANGUAGES_WITH_AUTO, filterEnabledLanguages } from '../utils/languages'
import { LanguageOptions } from './LanguageOptions'

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

  const allCodes = filterEnabledLanguages(LANGUAGES_WITH_AUTO, enabledLanguages)
  const userVisibleCount = allCodes.filter((code) => code !== 'auto').length
  const collapsedOnly = userVisibleCount === 1 && !includeAuto ? allCodes.find((code) => code !== 'auto') ?? null : null

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
      <LanguageOptions enabled={enabledLanguages} popular={popularLanguages} />
    </select>
  )
}
