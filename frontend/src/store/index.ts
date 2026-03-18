import { create } from 'zustand'
import type { FileInfo, TranscriptionResult, TranscriptionListItem, ConfigResponse, SummaryResult } from '../api/types'

interface AppState {
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
  transcriptionHistory: TranscriptionListItem[]
  setTranscriptionHistory: (list: TranscriptionListItem[]) => void
  currentTime: number
  setCurrentTime: (time: number) => void
  seekTo: number | null
  setSeekTo: (time: number | null) => void
  activeTab: string
  setActiveTab: (tab: string) => void
  reset: () => void
}

export const useStore = create<AppState>((set) => ({
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
  transcriptionHistory: [],
  setTranscriptionHistory: (list) => set({ transcriptionHistory: list }),
  currentTime: 0,
  setCurrentTime: (time) => set({ currentTime: time }),
  seekTo: null,
  setSeekTo: (time) => set({ seekTo: time }),
  activeTab: 'subtitles',
  setActiveTab: (tab) => set({ activeTab: tab }),
  reset: () => set({
    file: null, transcriptionId: null, transcriptionStatus: null,
    transcriptionResult: null, speakerMappings: {}, summary: null,
    currentTime: 0, seekTo: null, activeTab: 'subtitles',
  }),
}))
