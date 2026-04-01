import type {
  FileInfo, TranscriptionSettings, TranscriptionStatus,
  TranscriptionResult, TranscriptionListItem, ConfigResponse,
  RefinementResult,
  AnalysisTemplate, AnalysisGenerateRequest, AnalysisListItem, Utterance,
} from './types'

const BASE = import.meta.env.BASE_URL.replace(/\/$/, '')

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  if (response.redirected) {
    window.location.href = response.url
    throw new Error('Redirected to auth')
  }
  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      window.location.reload()
      throw new Error('Authentication required')
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || response.statusText)
  }
  return response.json()
}

export const api = {
  getConfig: () => request<ConfigResponse>('/api/config'),

  uploadFile: async (file: File): Promise<FileInfo> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch(`${BASE}/api/upload`, { method: 'POST', body: formData })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || response.statusText)
    }
    return response.json()
  },

  startTranscription: (settings: TranscriptionSettings) =>
    request<{ id: string; status: string }>('/api/transcribe', {
      method: 'POST',
      body: JSON.stringify(settings),
    }),

  getStatus: (id: string) => request<TranscriptionStatus>(`/api/status/${id}`),
  getTranscription: (id: string) => request<TranscriptionResult>(`/api/transcription/${id}`),

  exportTranscription: async (id: string, format: string): Promise<string> => {
    const response = await fetch(`${BASE}/api/transcription/${id}/export/${format}`)
    if (!response.ok) throw new Error('Export failed')
    return response.text()
  },

  saveTranscription: (id: string, utterances: import('./types').Utterance[]) =>
    request<{ status: string }>(`/api/transcription/${id}`, {
      method: 'PUT',
      body: JSON.stringify(utterances),
    }),

  updateSpeakers: (id: string, mappings: Record<string, string>) =>
    request<{ status: string }>(`/api/transcription/${id}/speakers`, {
      method: 'PUT',
      body: JSON.stringify({ mappings }),
    }),

  deleteTranscription: (id: string) =>
    request<{ status: string }>(`/api/transcription/${id}`, { method: 'DELETE' }),

  archiveTranscription: (id: string) =>
    request<{ status: string; expires_at: string }>(`/api/transcription/${id}/archive`, { method: 'POST' }),

  listTranscriptions: () => request<TranscriptionListItem[]>('/api/transcriptions'),

  renameFile: (fileId: string, filename: string) =>
    request<FileInfo>(`/api/files/${fileId}/rename`, {
      method: 'PATCH',
      body: JSON.stringify({ filename }),
    }),

  renameTitle: (id: string, title: string) =>
    request<{ status: string }>(`/api/transcription/${id}/title`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    }),

  generateRefinement: (id: string, context?: string) =>
    request<RefinementResult>(`/api/refine/${id}`, {
      method: 'POST',
      ...(context ? { body: JSON.stringify({ context }) } : {}),
    }),

  getRefinement: (id: string) =>
    request<RefinementResult>(`/api/refine/${id}`),

  deleteRefinement: (id: string) =>
    request<{ status: string }>(`/api/refine/${id}`, { method: 'DELETE' }),

  getAnalysisTemplates: () => request<AnalysisTemplate[]>('/api/analysis/templates'),

  listAnalyses: (transcriptionId: string) =>
    request<AnalysisListItem[]>(`/api/analysis/${transcriptionId}`),

  getAnalysis: (transcriptionId: string, analysisId: string) =>
    request<unknown>(`/api/analysis/${transcriptionId}/${analysisId}`),

  generateAnalysis: (transcriptionId: string, req: AnalysisGenerateRequest) =>
    request<unknown>(`/api/analysis/${transcriptionId}`, {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  deleteAnalysis: (transcriptionId: string, analysisId: string) =>
    request<void>(`/api/analysis/${transcriptionId}/${analysisId}`, { method: 'DELETE' }),

  deleteAnalysisItem: (transcriptionId: string, analysisId: string, field: string, index: number) =>
    request<unknown>(`/api/analysis/${transcriptionId}/${analysisId}/items/${field}/${index}`, { method: 'DELETE' }),

  translateTranscription: (id: string, targetLanguage: string) =>
    request<{ utterances: Utterance[], language: string }>(`/api/translate/${id}`, {
      method: 'POST',
      body: JSON.stringify({ target_language: targetLanguage }),
    }),

  getTranslation: (id: string) =>
    request<{ utterances: Utterance[], language: string }>(`/api/translate/${id}`),

  deleteTranslation: (id: string) =>
    request<{ status: string }>(`/api/translate/${id}`, { method: 'DELETE' }),

  getMediaUrl: (fileId: string) => `${BASE}/api/media/${fileId}`,
  getMediaFallbackUrl: (fileId: string) => `${BASE}/api/media/${fileId}/fallback`,

  connectWebSocket: (transcriptionId: string): WebSocket => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return new WebSocket(`${protocol}//${window.location.host}${BASE}/api/ws/status/${transcriptionId}`)
  },
}
