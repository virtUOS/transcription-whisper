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
}

export interface TranscriptionListItem {
  id: string
  file_id: string
  original_filename: string
  status: string
  language: string | null
  model: string | null
  created_at: string
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
}

export interface ConfigResponse {
  asr_backend: string
  whisper_models: string[]
  default_model: string
  llm_available: boolean
  logout_url: string
}

export interface ErrorResponse {
  error: string
  detail: string
}
