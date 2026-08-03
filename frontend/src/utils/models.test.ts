import { describe, expect, it } from 'vitest'
import { resolveModel, singleConfiguredModel } from './models'

describe('singleConfiguredModel', () => {
  it('returns the sole model when exactly one is configured', () => {
    expect(singleConfiguredModel(['large-v3-turbo'])).toBe('large-v3-turbo')
  })

  it('returns null when several models are configured', () => {
    expect(singleConfiguredModel(['base', 'large-v3'])).toBeNull()
  })

  it('returns null when no models are configured', () => {
    expect(singleConfiguredModel([])).toBeNull()
  })

  // WHISPER_MODELS="" (set but empty) makes backend/app/config.py's
  // split(",") yield [""], the one input where this returns a non-null
  // but falsy value. Consumers branch on truthiness, so a blank
  // configured model must not silently fall back.
  it('returns the blank string, not null, when the sole configured model is blank', () => {
    expect(singleConfiguredModel([''])).toBe('')
  })
})

describe('resolveModel', () => {
  it('pins to the sole configured model, ignoring the fallback', () => {
    expect(resolveModel(['large-v3-turbo'], 'large-v3')).toBe('large-v3-turbo')
  })

  it('uses the fallback when several models are configured', () => {
    expect(resolveModel(['base', 'large-v3'], 'large-v3')).toBe('large-v3')
  })

  it('uses the fallback when no models are configured', () => {
    expect(resolveModel([], 'base')).toBe('base')
  })

  // Same blank-model case as above: the fallback must not mask a
  // deliberately (if oddly) configured blank model.
  it('does not fall back when the sole configured model is blank', () => {
    expect(resolveModel([''], 'base')).toBe('')
  })
})
