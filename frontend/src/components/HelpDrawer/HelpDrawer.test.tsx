import { beforeEach, describe, expect, it } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { useStore } from '../../store'
import i18n from '../../i18n'
import { HelpDrawer } from './HelpDrawer'
import { settingValues } from './helpSections'
import type { ConfigResponse } from '../../api/types'

function buildConfig(overrides: Partial<ConfigResponse> = {}): ConfigResponse {
  return {
    asr_backend: 'whisperx',
    whisper_models: ['large-v3'],
    default_model: 'large-v3',
    llm_available: true,
    logout_url: '',
    popular_languages: [],
    enabled_languages: [],
    ...overrides,
  }
}

const initialState = useStore.getState()

beforeEach(async () => {
  useStore.setState(initialState, true)
  await i18n.changeLanguage('de')
})

function openHelp(config: ConfigResponse | null, section: string | null = null) {
  useStore.setState({ config, helpOpen: true, helpInitialSection: section })
  render(<HelpDrawer />)
}

describe('HelpDrawer', () => {
  it('shows no raw placeholders and no analysis entry without config', () => {
    openHelp(null, 'about')
    expect(document.body.textContent).not.toContain('{{')
    expect(screen.queryByRole('button', { name: 'Analyse' })).not.toBeInTheDocument()
  })

  it('hides the analysis entry when the LLM is unavailable', () => {
    openHelp(buildConfig({ llm_available: false }))
    expect(screen.queryByRole('button', { name: 'Analyse' })).not.toBeInTheDocument()
  })

  it('shows the analysis entry when the LLM is available', () => {
    openHelp(buildConfig({ llm_available: true }))
    expect(screen.getByRole('button', { name: 'Analyse' })).toBeInTheDocument()
  })

  it('falls back to getting-started for a gated initial section', () => {
    openHelp(buildConfig({ llm_available: false }), 'analysis')
    expect(screen.getByRole('button', { name: 'Einführung' })).toHaveClass('bg-gray-800')
  })

  it('fills the contact email into the about section', () => {
    openHelp(buildConfig({ contact_email: 'help@example.org' }), 'about')
    const sentence = screen.getByText(/Bei Fragen oder Problemen schreiben Sie an/)
    expect(sentence).toHaveTextContent('help@example.org')
    expect(sentence.querySelector('a[href="mailto:help@example.org"]')).not.toBeNull()
    expect(document.body.textContent).not.toContain('{{')
  })

  it('links the university legal pages', () => {
    openHelp(buildConfig())
    const expected = {
      'Datenschutzerklärung der Universität': 'https://www.uni-osnabrueck.de/datenschutzerklaerung',
      Impressum: 'https://www.uni-osnabrueck.de/impressum',
      Barrierefreiheit: 'https://www.uni-osnabrueck.de/barrierefreiheit',
    }
    for (const [name, href] of Object.entries(expected)) {
      const link = screen.getByRole('link', { name })
      expect(link).toHaveAttribute('href', href)
      expect(link).toHaveAttribute('target', '_blank')
      expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    }
  })
})

describe('HelpDrawer screenshots', () => {
  it('keeps the drawer open on Escape while a lightbox is open, closes it otherwise', () => {
    openHelp(buildConfig(), 'archive')
    const dialog = document.querySelector('dialog') as HTMLDialogElement
    expect(dialog).not.toBeNull()
    dialog.setAttribute('open', '')
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(useStore.getState().helpOpen).toBe(true)
    dialog.removeAttribute('open')
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(useStore.getState().helpOpen).toBe(false)
  })

  it('renders screenshots outside paragraphs', () => {
    openHelp(buildConfig(), 'archive')
    expect(document.querySelector('p figure, p dialog, p button')).toBeNull()
    expect(document.querySelector('figure')).not.toBeNull()
  })
})

describe('settingValues', () => {
  it('converts expiry hours to days', () => {
    const values = settingValues(
      buildConfig({ default_expiry_hours: 72, archive_expiry_hours: 4320 }),
      'de',
    )
    expect(values.retention_days).toBe('3')
    expect(values.archive_retention_days).toBe('180')
  })

  it('formats fractional days per language', () => {
    expect(settingValues(buildConfig({ default_expiry_hours: 36 }), 'de').retention_days).toBe('1,5')
    expect(settingValues(buildConfig({ default_expiry_hours: 36 }), 'en').retention_days).toBe('1.5')
  })

  it('passes the default model and token expiry through', () => {
    const values = settingValues(
      buildConfig({ default_model: 'large-v3', api_token_default_expiry_days: 90 }),
      'en',
    )
    expect(values.default_model).toBe('large-v3')
    expect(values.api_token_expiry_days).toBe('90')
  })

  it('returns an empty object without config', () => {
    expect(settingValues(null, 'de')).toEqual({})
  })
})
