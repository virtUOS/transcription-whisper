import { describe, expect, it } from 'vitest'
import i18n from '../i18n'
import { ApiError } from '../api/client'
import { analysisErrorMessage } from './analysisError'

const t = i18n.t.bind(i18n)

describe('analysisErrorMessage', () => {
  // The server answers 422 when the reply reached the model's output limit.
  // Retrying cannot help, so the user needs to hear why, in their language,
  // rather than the server's English detail or a bare "Internal Server Error".
  it('explains a reply that reached the output limit, in every UI language', async () => {
    for (const lng of ['en', 'de']) {
      await i18n.changeLanguage(lng)
      const message = analysisErrorMessage(new ApiError(422, 'server detail'), t)
      expect(message).not.toBe('analysis.outputLimitExceeded')
      expect(message).not.toBe('server detail')
      expect(message).toBe(i18n.getResource(lng, 'translation', 'analysis.outputLimitExceeded'))
    }
  })

  it('shows the server detail for any other API error', () => {
    expect(analysisErrorMessage(new ApiError(429, 'Analysis generation already in progress'), t))
      .toBe('Analysis generation already in progress')
  })

  it('falls back to the generic failure text for a non-Error', () => {
    expect(analysisErrorMessage('boom', t)).toBe(t('analysis.generationFailed'))
  })
})
