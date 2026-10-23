import { describe, expect, it } from 'vitest'
import { fillSettings, formatDays, placeholdersIn, toSentinels } from './helpText'

describe('helpText', () => {
  it('fills placeholders and blanks missing values', () => {
    expect(
      fillSettings('Mail {{contact_email}}, {{retention_days}} Tage', {
        contact_email: 'a@b',
        retention_days: '3',
      }),
    ).toBe('Mail a@b, 3 Tage')
    expect(fillSettings('x {{contact_email}} y', {})).toBe('x  y')
  })

  it('turns placeholders into sentinels', () => {
    expect(toSentinels('[{{contact_email}}](mailto:{{contact_email}})')).toBe(
      '[__TW_SETTING_contact_email__](mailto:__TW_SETTING_contact_email__)',
    )
  })

  it('lists placeholders in use', () => {
    expect(placeholdersIn('{{a}} {{default_model}}')).toEqual(['a', 'default_model'])
  })

  it('formats hours as days', () => {
    expect(formatDays(72, 'de')).toBe('3')
    expect(formatDays(4320, 'en')).toBe('180')
    expect(formatDays(36, 'de')).toBe('1,5')
    expect(formatDays(36, 'en')).toBe('1.5')
  })
})
