import { useTranslation } from 'react-i18next'
import { LANGUAGES, filterEnabledLanguages, partitionPopular } from '../utils/languages'

interface Props {
  enabled: readonly string[]
  popular: readonly string[]
}

/**
 * Renders `<option>` elements for the language list, with popular
 * languages promoted above a divider. Intended to be placed inside a
 * `<select>`, after any caller-supplied placeholder option.
 */
export function LanguageOptions({ enabled, popular }: Props) {
  const { t, i18n } = useTranslation()
  const codes = filterEnabledLanguages(LANGUAGES, enabled)
  const { popular: promoted, rest } = partitionPopular(codes, popular)
  const sortedRest = [...rest].sort((a, b) =>
    t(`languages.${a}`, a).localeCompare(t(`languages.${b}`, b), i18n.language),
  )
  return (
    <>
      {promoted.map((code) => (
        <option key={code} value={code}>{t(`languages.${code}`, code)}</option>
      ))}
      {promoted.length > 0 && sortedRest.length > 0 && <option disabled>{'───────────'}</option>}
      {sortedRest.map((code) => (
        <option key={code} value={code}>{t(`languages.${code}`, code)}</option>
      ))}
    </>
  )
}
