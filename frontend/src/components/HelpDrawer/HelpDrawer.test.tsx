import { beforeEach, describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { useStore } from '../../store'
import i18n from '../../i18n'
import { HelpDrawer } from './HelpDrawer'
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
    expect(screen.getAllByText(/help@example\.org/).length).toBeGreaterThan(0)
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
