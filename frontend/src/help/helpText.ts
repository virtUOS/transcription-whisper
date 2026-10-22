/**
 * Placeholder helpers for help markdown. Imported by Node scripts, so: no Vite
 * APIs, no non-erasable TypeScript syntax.
 */

export const SETTING_KEYS = [
  'contact_email',
  'retention_days',
  'archive_retention_days',
  'default_model',
  'api_token_expiry_days',
] as const

export type SettingKey = (typeof SETTING_KEYS)[number]

export type SettingValues = Partial<Record<SettingKey, string>>

const PLACEHOLDER = /\{\{(\w+)\}\}/g

/** Replace `{{key}}` with its value; a missing value becomes the empty string. */
export function fillSettings(markdown: string, values: SettingValues): string {
  const lookup: Record<string, string | undefined> = values
  return markdown.replace(PLACEHOLDER, (_m, key: string) => lookup[key] ?? '')
}

/** Replace `{{key}}` with the sentinel `__TW_SETTING_key__`. */
export function toSentinels(markdown: string): string {
  return markdown.replace(PLACEHOLDER, (_m, key: string) => `__TW_SETTING_${key}__`)
}

/** Every placeholder key used, in order of appearance (repeats included). */
export function placeholdersIn(markdown: string): string[] {
  return [...markdown.matchAll(PLACEHOLDER)].map((m) => m[1])
}

/** Hours as days, at most one decimal, no trailing `.0`, decimal comma for German. */
export function formatDays(hours: number, lang: 'de' | 'en'): string {
  const days = Math.round((hours / 24) * 10) / 10
  const text = String(days)
  return lang === 'de' ? text.replace('.', ',') : text
}
