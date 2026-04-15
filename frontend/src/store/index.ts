import { create } from 'zustand'
import type { FileInfo, TranscriptionResult, TranscriptionListItem, ConfigResponse, Utterance, RefinementMetadata, AnalysisListItem, TranscriptionPreset, AnalysisPreset, RefinementPreset, PresetBundle } from '../api/types'

type AppView = 'archive' | 'upload' | 'record' | 'detail' | 'presets'

interface AppState {
  currentView: AppView
  setCurrentView: (view: AppView) => void
  config: ConfigResponse | null
  setConfig: (config: ConfigResponse) => void
  file: FileInfo | null
  setFile: (file: FileInfo | null) => void
  uploading: boolean
  setUploading: (uploading: boolean) => void
  uploadAbortController: AbortController | null
  setUploadAbortController: (controller: AbortController | null) => void
  confirmLeaveUpload: (message: string) => boolean
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
  // Presets
  transcriptionPresets: TranscriptionPreset[]
  analysisPresets: AnalysisPreset[]
  refinementPresets: RefinementPreset[]
  bundles: PresetBundle[]
  activeBundleId: string | null
  setTranscriptionPresets: (presets: TranscriptionPreset[]) => void
  setAnalysisPresets: (presets: AnalysisPreset[]) => void
  setRefinementPresets: (presets: RefinementPreset[]) => void
  setBundles: (bundles: PresetBundle[]) => void
  setActiveBundleId: (id: string | null) => void
  clearRefinement: () => void
  reset: () => void
}

let isPopStateNavigation = false

export function setPopStateFlag(value: boolean) {
  isPopStateNavigation = value
}

export const useStore = create<AppState>((set, get) => ({
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
  uploading: false,
  setUploading: (uploading) => set({ uploading }),
  uploadAbortController: null,
  setUploadAbortController: (controller) => set({ uploadAbortController: controller }),
  confirmLeaveUpload: (message) => {
    if (!get().uploading) return true
    if (!window.confirm(message)) return false
    // Re-read state after the (synchronous) confirm dialog — upload may have
    // completed while the dialog was open.
    const state = get()
    if (state.uploading && state.uploadAbortController) {
      state.uploadAbortController.abort()
    }
    set({ uploading: false, uploadAbortController: null })
    return true
  },
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
  // Presets
  transcriptionPresets: [],
  analysisPresets: [],
  refinementPresets: [],
  bundles: [],
  activeBundleId: null,
  setTranscriptionPresets: (presets) => set({ transcriptionPresets: presets }),
  setAnalysisPresets: (presets) => set({ analysisPresets: presets }),
  setRefinementPresets: (presets) => set({ refinementPresets: presets }),
  setBundles: (bundles) => set({ bundles }),
  setActiveBundleId: (id) => set({ activeBundleId: id }),
  clearRefinement: () => set({ refinedUtterances: null, refinementMetadata: null, activeView: 'original' as const }),
  reset: () => set({
    currentView: 'archive' as const,
    file: null, uploading: false, uploadAbortController: null, transcriptionId: null, transcriptionTitle: null, transcriptionStatus: null,
    transcriptionResult: null, speakerMappings: {},
    currentTime: 0, seekTo: null, activeTab: 'subtitles', unsavedEdits: false,
    refinedUtterances: null, refinementMetadata: null, activeView: 'original' as const,
    translatedUtterances: null, translationLanguage: null,
    analyses: [],
  }),
}))

// Set initial browser history state
history.replaceState({ view: 'archive' }, '', '')
