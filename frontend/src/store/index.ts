import { create } from 'zustand'
import type { FileInfo, TranscriptionResult, TranscriptionListItem, ConfigResponse, SummaryResult, ProtocolResult, Utterance, RefinementMetadata } from '../api/types'

type AppView = 'archive' | 'upload' | 'record' | 'detail'

interface AppState {
  currentView: AppView
  setCurrentView: (view: AppView) => void
  config: ConfigResponse | null
  setConfig: (config: ConfigResponse) => void
  file: FileInfo | null
  setFile: (file: FileInfo | null) => void
  transcriptionId: string | null
  transcriptionStatus: string | null
  transcriptionResult: TranscriptionResult | null
  setTranscriptionId: (id: string | null) => void
  setTranscriptionStatus: (status: string | null) => void
  setTranscriptionResult: (result: TranscriptionResult | null) => void
  speakerMappings: Record<string, string>
  setSpeakerMappings: (mappings: Record<string, string>) => void
  summary: SummaryResult | null
  setSummary: (summary: SummaryResult | null) => void
  protocol: ProtocolResult | null
  setProtocol: (protocol: ProtocolResult | null) => void
  transcriptionHistory: TranscriptionListItem[]
  setTranscriptionHistory: (list: TranscriptionListItem[]) => void
  currentTime: number
  setCurrentTime: (time: number) => void
  seekTo: number | null
  setSeekTo: (time: number | null) => void
  activeTab: string
  setActiveTab: (tab: string) => void
  unsavedEdits: boolean
  setUnsavedEdits: (dirty: boolean) => void
  refinedUtterances: Utterance[] | null
  refinementMetadata: RefinementMetadata | null
  activeView: 'original' | 'refined' | 'translated'
  setRefinedUtterances: (utterances: Utterance[] | null) => void
  setRefinementMetadata: (metadata: RefinementMetadata | null) => void
  setActiveView: (view: 'original' | 'refined' | 'translated') => void
  translatedUtterances: Utterance[] | null
  translationLanguage: string | null
  setTranslatedUtterances: (utterances: Utterance[] | null) => void
  setTranslationLanguage: (language: string | null) => void
  clearTranslation: () => void
  analysisResult: unknown | null
  analysisTemplate: string | null
  analysisPrompt: string | null
  setAnalysisResult: (result: unknown | null) => void
  setAnalysisTemplate: (template: string | null) => void
  setAnalysisPrompt: (prompt: string | null) => void
  clearRefinement: () => void
  reset: () => void
}

export const useStore = create<AppState>((set) => ({
  currentView: 'archive' as const,
  setCurrentView: (view) => set({ currentView: view }),
  config: null,
  setConfig: (config) => set({ config }),
  file: null,
  setFile: (file) => set({ file }),
  transcriptionId: null,
  transcriptionStatus: null,
  transcriptionResult: null,
  setTranscriptionId: (id) => set({ transcriptionId: id }),
  setTranscriptionStatus: (status) => set({ transcriptionStatus: status }),
  setTranscriptionResult: (result) => set({ transcriptionResult: result }),
  speakerMappings: {},
  setSpeakerMappings: (mappings) => set({ speakerMappings: mappings }),
  summary: null,
  setSummary: (summary) => set({ summary }),
  protocol: null,
  setProtocol: (protocol) => set({ protocol }),
  transcriptionHistory: [],
  setTranscriptionHistory: (list) => set({ transcriptionHistory: list }),
  currentTime: 0,
  setCurrentTime: (time) => set({ currentTime: time }),
  seekTo: null,
  setSeekTo: (time) => set({ seekTo: time }),
  activeTab: 'subtitles',
  setActiveTab: (tab) => set({ activeTab: tab }),
  unsavedEdits: false,
  setUnsavedEdits: (dirty) => set({ unsavedEdits: dirty }),
  refinedUtterances: null,
  refinementMetadata: null,
  activeView: 'original' as const,
  setRefinedUtterances: (utterances) => set({ refinedUtterances: utterances }),
  setRefinementMetadata: (metadata) => set({ refinementMetadata: metadata }),
  setActiveView: (view) => set({ activeView: view }),
  translatedUtterances: null,
  translationLanguage: null,
  setTranslatedUtterances: (utterances) => set({ translatedUtterances: utterances }),
  setTranslationLanguage: (language) => set({ translationLanguage: language }),
  clearTranslation: () => set({ translatedUtterances: null, translationLanguage: null, activeView: 'original' as const }),
  analysisResult: null,
  analysisTemplate: null,
  analysisPrompt: null,
  setAnalysisResult: (result) => set({ analysisResult: result }),
  setAnalysisTemplate: (template) => set({ analysisTemplate: template }),
  setAnalysisPrompt: (prompt) => set({ analysisPrompt: prompt }),
  clearRefinement: () => set({ refinedUtterances: null, refinementMetadata: null, activeView: 'original' as const }),
  reset: () => set({
    currentView: 'archive' as const,
    file: null, transcriptionId: null, transcriptionStatus: null,
    transcriptionResult: null, speakerMappings: {}, summary: null, protocol: null,
    currentTime: 0, seekTo: null, activeTab: 'subtitles', unsavedEdits: false,
    refinedUtterances: null, refinementMetadata: null, activeView: 'original' as const,
    translatedUtterances: null, translationLanguage: null,
    analysisResult: null, analysisTemplate: null, analysisPrompt: null,
  }),
}))
