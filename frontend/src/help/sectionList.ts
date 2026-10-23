/**
 * Ordered list of help sections, shared by the in-app drawer and the public
 * static guide. Imported by Node scripts, so: no Vite APIs, no non-erasable
 * TypeScript syntax, explicit `.ts` extensions on local imports.
 */

export type HelpFeature = 'llm' | 'api_tokens'

export type HelpSectionId =
  | 'about'
  | 'getting-started'
  | 'archive'
  | 'upload'
  | 'record'
  | 'transcription-settings'
  | 'subtitle-editor'
  | 'speaker-mapping'
  | 'analysis'
  | 'translation'
  | 'refinement'
  | 'format-viewer'
  | 'presets'
  | 'bundles'
  | 'api-access'

export interface HelpSection {
  id: HelpSectionId
  filename: string
  /** Section is only shown when this feature is enabled. */
  feature?: HelpFeature
}

export const sections: readonly HelpSection[] = [
  { id: 'about', filename: '00-about.md' },
  { id: 'getting-started', filename: '01-getting-started.md' },
  { id: 'archive', filename: '02-archive.md' },
  { id: 'upload', filename: '03-upload.md' },
  { id: 'record', filename: '04-record.md' },
  { id: 'transcription-settings', filename: '05-transcription-settings.md' },
  { id: 'subtitle-editor', filename: '06-subtitle-editor.md' },
  { id: 'speaker-mapping', filename: '07-speaker-mapping.md' },
  { id: 'analysis', filename: '08-analysis.md', feature: 'llm' },
  { id: 'translation', filename: '09-translation.md', feature: 'llm' },
  { id: 'refinement', filename: '10-refinement.md', feature: 'llm' },
  { id: 'format-viewer', filename: '11-format-viewer.md' },
  { id: 'presets', filename: '12-presets.md' },
  { id: 'bundles', filename: '13-bundles.md', feature: 'llm' },
  { id: 'api-access', filename: '14-api-access.md', feature: 'api_tokens' },
]
