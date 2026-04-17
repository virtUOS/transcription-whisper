export const LANGUAGES = [
  'af', 'am', 'ar', 'as', 'az',
  'ba', 'be', 'bg', 'bn', 'bo', 'br', 'bs',
  'ca', 'cs', 'cy',
  'da', 'de',
  'el', 'en', 'es', 'et', 'eu',
  'fa', 'fi', 'fo', 'fr',
  'gl', 'gu',
  'ha', 'haw', 'he', 'hi', 'hr', 'ht', 'hu', 'hy',
  'id', 'is', 'it',
  'ja', 'jw',
  'ka', 'kk', 'km', 'kn', 'ko',
  'la', 'lb', 'ln', 'lo', 'lt', 'lv',
  'mg', 'mi', 'mk', 'ml', 'mn', 'mr', 'ms', 'mt', 'my',
  'ne', 'nl', 'nn', 'no',
  'oc',
  'pa', 'pl', 'ps', 'pt',
  'ro', 'ru',
  'sa', 'sd', 'si', 'sk', 'sl', 'sn', 'so', 'sq', 'sr', 'su', 'sv', 'sw',
  'ta', 'te', 'tg', 'th', 'tk', 'tl', 'tr', 'tt',
  'uk', 'ur', 'uz',
  'vi',
  'yi', 'yo', 'yue',
  'zh',
] as const

export const LANGUAGES_WITH_AUTO = ['auto', ...LANGUAGES] as const

/**
 * Filter a list of language codes through an allowlist.
 * Empty allowlist (length 0) is the "no restriction" sentinel → return the full list.
 * The special 'auto' code is always kept when present in the input list, regardless of allowlist.
 */
export function filterEnabledLanguages<T extends string>(
  list: readonly T[],
  enabled: readonly string[],
): T[] {
  if (enabled.length === 0) return [...list]
  return list.filter((code) => code === 'auto' || enabled.includes(code))
}

/**
 * Check whether a single language code is enabled by the allowlist.
 * Empty allowlist means all codes are enabled.
 */
export function isLanguageEnabled(code: string, enabled: readonly string[]): boolean {
  if (enabled.length === 0) return true
  return enabled.includes(code)
}

/**
 * Split a filtered language list into popular-first and rest groups,
 * preserving the order of `popular` for the promoted codes. The 'auto'
 * sentinel is excluded from both groups since it is rendered separately.
 */
export function partitionPopular<T extends string>(
  codes: readonly T[],
  popular: readonly string[],
): { popular: T[]; rest: T[] } {
  const promoted = popular.filter((code): code is T => codes.includes(code as T))
  const rest = codes.filter((code) => code !== 'auto' && !promoted.includes(code))
  return { popular: promoted, rest }
}
