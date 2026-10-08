import type { TFunction } from 'i18next'
import { ApiError } from '../api/client'

/**
 * The message to show when generating an analysis fails.
 *
 * The server answers 422 when the reply reached the model's output limit. The
 * same request reaches it again, so the user is told why, in their language,
 * instead of the server's English detail.
 */
export function analysisErrorMessage(e: unknown, t: TFunction): string {
  if (e instanceof ApiError && e.status === 422) return t('analysis.outputLimitExceeded')
  return e instanceof Error ? e.message : t('analysis.generationFailed')
}
