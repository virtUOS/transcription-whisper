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

  // The server sends code "malformed_reply" when every attempt at a reply was
  // unusable. Trying again can help, so the user hears that, in their language.
  it('explains a malformed reply, in every UI language', async () => {
    for (const lng of ['en', 'de']) {
      await i18n.changeLanguage(lng)
      const message = analysisErrorMessage(new ApiError(502, 'server detail', 'malformed_reply'), t)
      expect(message).not.toBe('analysis.malformedReply')
      expect(message).not.toBe('server detail')
      expect(message).toBe(i18n.getResource(lng, 'translation', 'analysis.malformedReply'))
    }
  })

  // The proxy answers 502 itself when the app is down. That is not a model
  // reply, so the status alone must not produce the malformed-reply text.
  it('does not call a 502 without the code a malformed reply', async () => {
    await i18n.changeLanguage('en')
    expect(analysisErrorMessage(new ApiError(502, 'Bad Gateway'), t)).toBe('Bad Gateway')
  })

  it('shows the server detail for any other API error', () => {
    expect(analysisErrorMessage(new ApiError(429, 'Analysis generation already in progress'), t))
      .toBe('Analysis generation already in progress')
  })

  it('falls back to the generic failure text for a non-Error', () => {
    expect(analysisErrorMessage('boom', t)).toBe(t('analysis.generationFailed'))
  })
})
