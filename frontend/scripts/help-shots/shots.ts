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

/**
 * Select a file in the upload dropzone and wait until the upload has landed:
 * the response arrived and the dropzone (which holds #file-upload) is replaced
 * by the compact file row. The settings panel and start button render earlier,
 * while the spinner dropzone is still tall, so waiting for them is not enough.
 */
export async function uploadFile(page: Page, path: string): Promise<void> {
  const uploaded = page.waitForResponse((r) => r.url().includes('/api/upload') && r.ok())
  await page.locator('#file-upload').setInputFiles(path)
  await uploaded
  await page.locator('#file-upload').waitFor({ state: 'detached' })
}

export const shots: ShotSpec[] = [
  {
    id: 'upload',
    async prepare(page) {
      await page.locator('[data-help="new-upload"]').click()
      await uploadFile(page, audioFile())
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
