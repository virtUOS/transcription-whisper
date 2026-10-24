import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { useStore } from '../../store'
import i18n from '../../i18n'
import { api } from '../../api/client'
import { PresetsPage } from './PresetsPage'
import type { ConfigResponse, TranscriptionPreset } from '../../api/types'

vi.mock('../../api/client', () => ({
  api: {
    createTranscriptionPreset: vi.fn(),
    updateTranscriptionPreset: vi.fn(),
  },
}))

const config: ConfigResponse = {
  asr_backend: 'whisperx',
  whisper_models: ['large-v3-turbo'],
  default_model: 'large-v3-turbo',
  llm_available: false,
  logout_url: '',
  popular_languages: [],
  enabled_languages: [],
}

function buildPreset(overrides: Partial<TranscriptionPreset> = {}): TranscriptionPreset {
  return {
    id: 'p1',
    name: 'Interview',
    language: null,
    model: 'large-v3-turbo',
    min_speakers: 2,
    max_speakers: 4,
    initial_prompt: null,
    hotwords: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  }
}

function renderPage(presets: TranscriptionPreset[] = []) {
  useStore.setState({ config, transcriptionPresets: presets })
  render(<PresetsPage />)
}

const initialState = useStore.getState()

beforeEach(async () => {
  vi.clearAllMocks()
  useStore.setState(initialState, true)
  await i18n.changeLanguage('en')
})

describe('PresetsPage — transcription preset speakers', () => {
  it('a new transcription preset saves speaker detection on with 1–2 speakers', async () => {
    vi.mocked(api.createTranscriptionPreset).mockResolvedValue(buildPreset())
    renderPage()

    fireEvent.click(screen.getByRole('button', { name: /New preset/ }))
    fireEvent.change(screen.getByPlaceholderText('Preset name'), { target: { value: 'Mine' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(api.createTranscriptionPreset).toHaveBeenCalled())
    expect(api.createTranscriptionPreset).toHaveBeenCalledWith(
      expect.objectContaining({ min_speakers: 1, max_speakers: 2 }),
    )
  })

  it('editing a preset keeps its speaker counts', async () => {
    vi.mocked(api.updateTranscriptionPreset).mockResolvedValue(buildPreset({ name: 'Renamed' }))
    renderPage([buildPreset()])

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    fireEvent.change(screen.getByDisplayValue('Interview'), { target: { value: 'Renamed' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(api.updateTranscriptionPreset).toHaveBeenCalled())
    expect(api.updateTranscriptionPreset).toHaveBeenCalledWith(
      'p1',
      expect.objectContaining({ name: 'Renamed', min_speakers: 2, max_speakers: 4 }),
    )
  })

  it('switching detection off saves 0/0', async () => {
    vi.mocked(api.updateTranscriptionPreset).mockResolvedValue(buildPreset({ min_speakers: 0, max_speakers: 0 }))
    renderPage([buildPreset()])

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    fireEvent.click(screen.getByRole('checkbox', { name: 'Detect speakers' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(api.updateTranscriptionPreset).toHaveBeenCalled())
    expect(api.updateTranscriptionPreset).toHaveBeenCalledWith(
      'p1',
      expect.objectContaining({ min_speakers: 0, max_speakers: 0 }),
    )
  })
})
