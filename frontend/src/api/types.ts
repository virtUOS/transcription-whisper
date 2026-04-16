export interface FileInfo {
  id: string
  original_filename: string
  media_type: string
  file_size: number
  has_video: boolean
}

export interface TranscriptionSettings {
  file_id: string
  language: string | null
  model: string
  min_speakers: number
  max_speakers: number
  initial_prompt: string | null
  hotwords: string | null
}

export interface TranscriptionStatus {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number | null
  error: string | null
}

export interface Utterance {
  start: number
  end: number
  text: string
  speaker: string | null
}

export interface TranscriptionResult {
  id: string
  status: string
  utterances: Utterance[]
  text: string
  language: string | null
  speaker_mappings: Record<string, string>
  summary: SummaryResult | null
  protocol: ProtocolResult | null
}

export interface TranscriptionListItem {
  id: string
  file_id: string
  original_filename: string
  status: string
  language: string | null
  model: string | null
  created_at: string
  file_size: number
  expires_at: string
  archived: boolean
  title: string | null
  has_video: boolean
}

export interface ChapterHint {
  title?: string
  description?: string
}

export interface SummaryChapter {
  title: string
  start_time: number
  end_time: number
  summary: string
}

export interface SummaryResult {
  summary: string
  chapters: SummaryChapter[]
  chapter_hints?: ChapterHint[]
  language?: string | null
  llm_provider: string | null
  llm_model: string | null
}

export interface ProtocolKeyPoint {
  topic: string
  speaker: string
  timestamp: number | null
  content: string
}

export interface ProtocolDecision {
  decision: string
  timestamp: number | null
}

export interface ProtocolActionItem {
  task: string
  assignee: string
  timestamp: number | null
}

export interface ProtocolResult {
  title: string
  participants: string[]
  key_points: ProtocolKeyPoint[]
  decisions: ProtocolDecision[]
  action_items: ProtocolActionItem[]
  language?: string | null
  llm_provider: string | null
  llm_model: string | null
}

export interface RefinementMetadata {
  changed_indices: number[]
  changes_summary: string
  context: string | null
  llm_provider: string | null
  llm_model: string | null
  created_at: string | null
}

export interface RefinementResult {
  utterances: Utterance[]
  metadata: RefinementMetadata
}

export interface ConfigResponse {
  asr_backend: string
  whisper_models: string[]
  default_model: string
  llm_available: boolean
  logout_url: string
  popular_languages: string[]
  enabled_languages: string[]
}

export interface AnalysisTemplate {
  id: string
  name: string
  description: string
  default_prompt: string
}

export interface AnalysisGenerateRequest {
  template?: string | null
  custom_prompt?: string | null
  language?: string | null
  chapter_hints?: ChapterHint[] | null
  agenda?: string | null
}

export interface AnalysisListItem {
  id: string
  template: string | null
  language: string | null
  llm_provider: string | null
  llm_model: string | null
  created_at: string | null
}

export interface ErrorResponse {
  error: string
  detail: string
}

// --- Presets ---

export interface TranscriptionPreset {
  id: string
  name: string
  language: string | null
  model: string
  min_speakers: number
  max_speakers: number
  initial_prompt: string | null
  hotwords: string | null
  created_at: string | null
  updated_at: string | null
}

export interface TranscriptionPresetCreate {
  name: string
  language?: string | null
  model?: string
  min_speakers?: number
  max_speakers?: number
  initial_prompt?: string | null
  hotwords?: string | null
}

export interface AnalysisPreset {
  id: string
  name: string
  template: string | null
  custom_prompt: string | null
  language: string | null
  chapter_hints: ChapterHint[] | null
  agenda: string | null
  created_at: string | null
  updated_at: string | null
}

export interface AnalysisPresetCreate {
  name: string
  template?: string | null
  custom_prompt?: string | null
  language?: string | null
  chapter_hints?: ChapterHint[] | null
  agenda?: string | null
}

export interface RefinementPreset {
  id: string
  name: string
  context: string | null
  created_at: string | null
  updated_at: string | null
}

export interface RefinementPresetCreate {
  name: string
  context?: string | null
}

export interface PresetBundle {
  id: string
  name: string
  transcription_preset_id: string | null
  analysis_preset_id: string | null
  refinement_preset_id: string | null
  translate_language: string | null
  is_default: boolean
  created_at: string | null
  updated_at: string | null
}

export interface PresetBundleCreate {
  name: string
  transcription_preset_id?: string | null
  analysis_preset_id?: string | null
  refinement_preset_id?: string | null
  translate_language?: string | null
}

export interface PresetBundleExpanded extends PresetBundle {
  transcription_preset: TranscriptionPreset | null
  analysis_preset: AnalysisPreset | null
  refinement_preset: RefinementPreset | null
}
