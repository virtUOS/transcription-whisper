import { beforeEach, describe, expect, it } from 'vitest'
import { useStore } from './index'

describe('clearTranscriptionState', () => {
  beforeEach(() => {
    useStore.getState().reset()
  })

  it("drops the previous transcription's edits, views, refinement, translation and analyses", () => {
    useStore.setState({
      transcriptionResult: { id: 't1' } as never,
      speakerMappings: { SPEAKER_00: 'Ann' },
      currentTime: 12,
      seekTo: 5,
      activeTab: 'analysis' as never,
      unsavedEdits: true,
      refinedUtterances: [{ start: 0, end: 1, text: 'r' }] as never,
      refinementMetadata: { model: 'm' } as never,
      refinementStale: true,
      activeView: 'translated',
      translatedUtterances: [{ start: 0, end: 1, text: 't' }] as never,
      translationLanguage: 'de',
      translationSource: 'refined' as never,
      translationStale: true,
      translationSourceAvailable: false,
      analyses: [{ id: 'a1' }] as never,
    })

    useStore.getState().clearTranscriptionState()

    const s = useStore.getState()
    expect(s.transcriptionResult).toBeNull()
    expect(s.speakerMappings).toEqual({})
    expect(s.currentTime).toBe(0)
    expect(s.seekTo).toBeNull()
    expect(s.activeTab).toBe('subtitles')
    expect(s.unsavedEdits).toBe(false)
    expect(s.refinedUtterances).toBeNull()
    expect(s.refinementMetadata).toBeNull()
    expect(s.refinementStale).toBe(false)
    expect(s.activeView).toBe('original')
    expect(s.translatedUtterances).toBeNull()
    expect(s.translationLanguage).toBeNull()
    expect(s.translationSource).toBeNull()
    expect(s.translationStale).toBe(false)
    expect(s.translationSourceAvailable).toBe(true)
    expect(s.analyses).toEqual([])
  })
})
