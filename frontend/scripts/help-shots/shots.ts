import type { Page } from 'playwright'

export interface ShotSpec {
  id: string
  /** Bring the page (already loaded at the app root, language set) into the state to capture. */
  prepare(page: Page, lang: 'de' | 'en'): Promise<void>
  /** CSS selector of the element whose box is the screenshot clip. */
  clip: string
  /** CSS selectors of the numbered markers, in marker order. */
  marks: string[]
}

/** Path of a tiny generated audio file; the runner sets it before any spec runs. */
function audioFile(): string {
  const path = process.env.HELP_SHOTS_AUDIO
  if (!path) throw new Error('HELP_SHOTS_AUDIO is not set (the runner provides it)')
  return path
}

export const shots: ShotSpec[] = [
  {
    id: 'upload',
    async prepare(page) {
      await page.locator('[data-help="new-upload"]').click()
      await page.locator('#file-upload').setInputFiles(audioFile())
      // The settings panel and the start button appear once the upload finished.
      await page.locator('[data-help="transcribe-start"]').waitFor()
      await page.locator('#upload-model-field').waitFor()
    },
    clip: '#root',
    marks: [
      '#upload-language-field',
      '#upload-model-field',
      '[data-help="upload-speakers"]',
      '[data-help="transcribe-start"]',
    ],
  },
]
