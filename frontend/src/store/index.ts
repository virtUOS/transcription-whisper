import { create } from 'zustand'
import type { FileInfo, TranscriptionResult, TranscriptionListItem, ConfigResponse, Utterance, RefinementMetadata, AnalysisListItem } from '../api/types'

type AppView = 'archive' | 'upload' | 'record' | 'detail'

interface AppState {
  currentView: AppView
  setCurrentView: (view: AppView) => void
  config: ConfigResponse | null
  setConfig: (config: ConfigResponse) => void
  file: FileInfo | null
  setFile: (file: FileInfo | null) => void
  transcriptionId: string | null
  transcriptionTitle: string | null
  transcriptionStatus: string | null
  transcriptionResult: TranscriptionResult | null
  setTranscriptionId: (id: string | null) => void
  setTranscriptionTitle: (title: string | null) => void
  setTranscriptionStatus: (status: string | null) => void
  setTranscriptionResult: (result: TranscriptionResult | null) => void
  speakerMappings: Record<string, string>
  setSpeakerMappings: (mappings: Record<string, string>) => void
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
  analyses: AnalysisListItem[]
  setAnalyses: (analyses: AnalysisListItem[]) => void
  addAnalysis: (item: AnalysisListItem) => void
  removeAnalysis: (id: string) => void
  clearRefinement: () => void
  reset: () => void
}

let isPopStateNavigation = false

export function setPopStateFlag(value: boolean) {
  isPopStateNavigation = value
}

export const useStore = create<AppState>((set) => ({
  currentView: 'archive' as const,
  setCurrentView: (view) => {
    const current = useStore.getState().currentView
    if (view !== current && !isPopStateNavigation) {
      history.pushState({ view }, '', '')
    }
    set({ currentView: view })
  },
  config: null,
  setConfig: (config) => set({ config }),
  file: null,
  setFile: (file) => set({ file }),
  transcriptionId: null,
  transcriptionTitle: null,
  transcriptionStatus: null,
  transcriptionResult: null,
  setTranscriptionId: (id) => set({ transcriptionId: id }),
  setTranscriptionTitle: (title) => set({ transcriptionTitle: title }),
  setTranscriptionStatus: (status) => set({ transcriptionStatus: status }),
  setTranscriptionResult: (result) => set({ transcriptionResult: result }),
  speakerMappings: {},
  setSpeakerMappings: (mappings) => set({ speakerMappings: mappings }),
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
  analyses: [],
  setAnalyses: (analyses) => set({ analyses }),
  addAnalysis: (item) => set((s) => ({ analyses: [item, ...s.analyses] })),
  removeAnalysis: (id) => set((s) => ({ analyses: s.analyses.filter((a) => a.id !== id) })),
  clearRefinement: () => set({ refinedUtterances: null, refinementMetadata: null, activeView: 'original' as const }),
  reset: () => set({
    currentView: 'archive' as const,
    file: null, transcriptionId: null, transcriptionTitle: null, transcriptionStatus: null,
    transcriptionResult: null, speakerMappings: {},
    currentTime: 0, seekTo: null, activeTab: 'subtitles', unsavedEdits: false,
    refinedUtterances: null, refinementMetadata: null, activeView: 'original' as const,
    translatedUtterances: null, translationLanguage: null,
    analyses: [],
  }),
}))

// Set initial browser history state
history.replaceState({ view: 'archive' }, '', '')
