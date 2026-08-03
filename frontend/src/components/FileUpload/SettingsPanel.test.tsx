import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { useStore } from '../../store'
import i18n from '../../i18n'
import { SettingsPanel, type SettingsPanelValues } from './SettingsPanel'
import type { ConfigResponse } from '../../api/types'

function buildValues(overrides: Partial<SettingsPanelValues> = {}): SettingsPanelValues {
  return {
    language: 'auto',
    model: 'large-v3-turbo',
    detectSpeakers: false,
    minSpeakers: 1,
    maxSpeakers: 2,
    initialPrompt: '',
    hotwords: '',
    selectedPresetId: null,
    showAdvanced: false,
    ...overrides,
  }
}

function buildConfig(whisper_models: string[]): ConfigResponse {
  return {
    asr_backend: 'whisperx',
    whisper_models,
    default_model: whisper_models[0],
    llm_available: false,
    logout_url: '',
    popular_languages: [],
    enabled_languages: [],
  }
}

const initialState = useStore.getState()

beforeEach(() => {
  useStore.setState(initialState, true)
})

describe('SettingsPanel — model field', () => {
  it('shows the bare model name with a "Model" label when exactly one model is configured', () => {
    useStore.setState({ config: buildConfig(['large-v3-turbo']) })

    render(<SettingsPanel values={buildValues()} onChange={vi.fn()} />)

    const field = screen.getByRole('status', { name: 'Model' })
    expect(field.textContent).toBe('large-v3-turbo')
    expect(screen.queryByRole('combobox', { name: 'Quality' })).not.toBeInTheDocument()
  })

  it('shows the "Modell" label in German, still with the bare model name', async () => {
    await i18n.changeLanguage('de')

    useStore.setState({ config: buildConfig(['large-v3-turbo']) })

    render(<SettingsPanel values={buildValues()} onChange={vi.fn()} />)

    const field = screen.getByRole('status', { name: 'Modell' })
    expect(field.textContent).toBe('large-v3-turbo')

    await i18n.changeLanguage('en')
  })

  it('shows a "Quality" combobox with labeled options when several models are configured', () => {
    useStore.setState({ config: buildConfig(['base', 'large-v3-turbo', 'large-v3']) })

    render(<SettingsPanel values={buildValues({ model: 'large-v3-turbo' })} onChange={vi.fn()} />)

    const combobox = screen.getByRole('combobox', { name: 'Quality' })
    const options = within(combobox).getAllByRole('option').map((o) => o.textContent)
    expect(options).toEqual(['Standard (base)', 'Balanced (large-v3-turbo)', 'Best quality (large-v3)'])
    const selectedOption = within(combobox).getByRole('option', { name: 'Balanced (large-v3-turbo)' }) as HTMLOptionElement
    expect(selectedOption.selected).toBe(true)
    expect(combobox).toHaveValue('large-v3-turbo')
  })

  it('calls onChange with the selected model when a different option is picked', () => {
    const onChange = vi.fn()
    useStore.setState({ config: buildConfig(['base', 'large-v3-turbo', 'large-v3']) })

    render(<SettingsPanel values={buildValues({ model: 'large-v3-turbo' })} onChange={onChange} />)

    fireEvent.change(screen.getByRole('combobox', { name: 'Quality' }), { target: { value: 'large-v3' } })

    expect(onChange).toHaveBeenCalledWith({ model: 'large-v3' })
  })
})
