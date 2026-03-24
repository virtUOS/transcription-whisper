import type {
  FileInfo, TranscriptionSettings, TranscriptionStatus,
  TranscriptionResult, TranscriptionListItem, ConfigResponse,
  SummaryResult, ProtocolResult, ChapterHint, RefinementResult,
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

  listTranscriptions: () => request<TranscriptionListItem[]>('/api/transcriptions'),

  renameFile: (fileId: string, filename: string) =>
    request<FileInfo>(`/api/files/${fileId}/rename`, {
      method: 'PATCH',
      body: JSON.stringify({ filename }),
    }),

  generateSummary: (id: string, chapterHints?: ChapterHint[], language?: string) => {
    const options: RequestInit = { method: 'POST' }
    if (chapterHints?.length || language) {
      options.body = JSON.stringify({
        ...(chapterHints?.length ? { chapter_hints: chapterHints } : {}),
        ...(language ? { language } : {}),
      })
    }
    return request<SummaryResult>(`/api/summarize/${id}`, options)
  },

  deleteChapter: (id: string, chapterIndex: number) =>
    request<SummaryResult>(`/api/summarize/${id}/chapters/${chapterIndex}`, { method: 'DELETE' }),

  deleteSummary: (id: string) =>
    request<{ status: string }>(`/api/summarize/${id}`, { method: 'DELETE' }),

  generateProtocol: (id: string, language?: string) => {
    const options: RequestInit = { method: 'POST' }
    if (language) {
      options.body = JSON.stringify({ language })
    }
    return request<ProtocolResult>(`/api/protocol/${id}`, options)
  },

  deleteProtocol: (id: string) =>
    request<{ status: string }>(`/api/protocol/${id}`, { method: 'DELETE' }),

  generateRefinement: (id: string, context?: string) =>
    request<RefinementResult>(`/api/refine/${id}`, {
      method: 'POST',
      ...(context ? { body: JSON.stringify({ context }) } : {}),
    }),

  getRefinement: (id: string) =>
    request<RefinementResult>(`/api/refine/${id}`),

  deleteRefinement: (id: string) =>
    request<{ status: string }>(`/api/refine/${id}`, { method: 'DELETE' }),

  getMediaUrl: (fileId: string) => `${BASE}/api/media/${fileId}`,

  connectWebSocket: (transcriptionId: string): WebSocket => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return new WebSocket(`${protocol}//${window.location.host}${BASE}/api/ws/status/${transcriptionId}`)
  },
}
