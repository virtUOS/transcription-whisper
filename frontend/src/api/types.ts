export interface FileInfo {
  id: string
  original_filename: string
  media_type: string
  file_size: number
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
  live_transcription_available: boolean
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

export interface ErrorResponse {
  error: string
  detail: string
}

export interface LiveTranscriptionLine {
  speaker: string | null
  text: string
  start: number
  end: number
}

export interface LiveTranscriptionUpdate {
  type: 'transcription_update'
  lines: LiveTranscriptionLine[]
  buffer_text: string
}

export interface LiveSessionStarted {
  type: 'session_started'
  transcription_id: string
}

export interface LiveSessionComplete {
  type: 'session_complete'
  transcription_id: string
}

export interface LiveSessionError {
  type: 'error'
  detail: string
}

export interface LiveConfig {
  type: 'config'
  pcm_required: boolean
}

export type LiveMessage = LiveTranscriptionUpdate | LiveSessionStarted | LiveSessionComplete | LiveSessionError | LiveConfig
