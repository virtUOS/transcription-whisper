export const LANGUAGES = [
  'de', 'en', 'fr', 'es', 'it', 'pt', 'nl', 'pl', 'ru',
  'zh', 'ja', 'ko', 'ar', 'hi', 'tr', 'sv', 'da', 'fi', 'el',
  'he', 'hu', 'cs', 'ro', 'uk',
] as const

export const LANGUAGES_WITH_AUTO = ['auto', ...LANGUAGES] as const
