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
})
