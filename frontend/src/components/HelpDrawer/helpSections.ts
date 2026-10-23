/**
 * Single source of truth for help drawer sections.
 * - `sections` is the ordered list rendered in the sidebar.
 * - `viewToSection` maps the app's current view to its default help section.
 * - `loadContent(id, lang)` returns the raw markdown string for a section + language,
 *   or null if the file doesn't exist (e.g., en/de drift).
 * - `assetUrls` maps source asset paths to Vite-resolved URLs used by the markdown renderer.
 */

import { sections } from '../../help/sectionList.ts'
import type { HelpSectionId } from '../../help/sectionList.ts'

export { sections }
export type { HelpSection, HelpSectionId, HelpFeature } from '../../help/sectionList.ts'

import type { AppView } from '../../store'
import type { ConfigResponse } from '../../api/types'
import type { HelpSection } from '../../help/sectionList.ts'
import { fillSettings, formatDays } from '../../help/helpText.ts'
import type { SettingValues } from '../../help/helpText.ts'

export { fillSettings }

/** Sections whose feature is enabled on this host. Without config only ungated sections. */
export function visibleSections(config: ConfigResponse | null): readonly HelpSection[] {
  return sections.filter((s) => {
    if (s.feature === 'llm') return !!config?.llm_available
    if (s.feature === 'api_tokens') return !!config?.api_tokens_enabled
    return true
  })
}

/** Per-host values for the `{{...}}` placeholders; missing inputs are omitted. */
export function settingValues(config: ConfigResponse | null, lang: 'de' | 'en'): SettingValues {
  const values: SettingValues = {}
  if (!config) return values
  if (config.contact_email) values.contact_email = config.contact_email
  if (config.default_expiry_hours != null) values.retention_days = formatDays(config.default_expiry_hours, lang)
  if (config.archive_expiry_hours != null) values.archive_retention_days = formatDays(config.archive_expiry_hours, lang)
  if (config.default_model) values.default_model = config.default_model
  if (config.api_token_default_expiry_days != null) values.api_token_expiry_days = String(config.api_token_default_expiry_days)
  return values
}

export const viewToSection: Record<AppView, HelpSectionId> = {
  archive: 'getting-started',
  upload: 'upload',
  record: 'record',
  detail: 'subtitle-editor',
  presets: 'presets',
  settings: 'api-access',
}

// Vite glob: load every en/*.md and de/*.md as a raw string at build time.
// Both language bundles live in the same lazy chunk as the drawer, so language
// switching inside the drawer is instant.
const enMarkdown = import.meta.glob('/src/help/en/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

const deMarkdown = import.meta.glob('/src/help/de/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

// Vite glob: resolve asset URLs for SVG diagrams referenced from markdown.
// These are post-build URLs (e.g. "/assets/main-flow-abc123.svg").
export const assetUrls = import.meta.glob('/src/help/assets/*.{svg,png}', {
  query: '?url',
  import: 'default',
  eager: true,
}) as Record<string, string>

export function loadContent(id: HelpSectionId, lang: 'en' | 'de'): string | null {
  const section = sections.find((s) => s.id === id)
  if (!section) return null
  const map = lang === 'en' ? enMarkdown : deMarkdown
  const key = `/src/help/${lang}/${section.filename}`
  return map[key] ?? null
}
