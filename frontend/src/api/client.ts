import type {
  FileInfo, TranscriptionSettings, TranscriptionStatus,
  TranscriptionResult, TranscriptionListItem, ConfigResponse,
  SummaryResult, ProtocolResult,
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
  if (!response.ok) {
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

  listTranscriptions: () => request<TranscriptionListItem[]>('/api/transcriptions'),

  generateSummary: (id: string) =>
    request<SummaryResult>(`/api/summarize/${id}`, { method: 'POST' }),

  deleteSummary: (id: string) =>
    request<{ status: string }>(`/api/summarize/${id}`, { method: 'DELETE' }),

  generateProtocol: (id: string) =>
    request<ProtocolResult>(`/api/protocol/${id}`, { method: 'POST' }),

  deleteProtocol: (id: string) =>
    request<{ status: string }>(`/api/protocol/${id}`, { method: 'DELETE' }),

  getMediaUrl: (fileId: string) => `${BASE}/api/media/${fileId}`,

  connectWebSocket: (transcriptionId: string): WebSocket => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return new WebSocket(`${protocol}//${window.location.host}${BASE}/api/ws/status/${transcriptionId}`)
  },
}
