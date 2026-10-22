import { describe, expect, it } from 'vitest'
import de from './de.json'
import en from './en.json'
import { GENDERED_DE, GENDERED_EN } from './neutral'

function offenders(obj: unknown, re: RegExp, path = ''): string[] {
  if (typeof obj === 'string') return re.test(obj) ? [`${path}: ${obj}`] : []
  if (obj && typeof obj === 'object') {
    return Object.entries(obj).flatMap(([k, v]) => offenders(v, re, path ? `${path}.${k}` : k))
  }
  return []
}

describe('gender-neutral labels', () => {
  it('de.json has no gendered terms', () => {
    expect(offenders(de, GENDERED_DE)).toEqual([])
  })
  it('en.json has no gendered pronouns', () => {
    expect(offenders(en, GENDERED_EN)).toEqual([])
  })
})
