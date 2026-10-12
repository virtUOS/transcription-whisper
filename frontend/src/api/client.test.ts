import { describe, it, expect, vi } from 'vitest'
import { ApiError, api } from './client'

describe('ApiError', () => {
  it('keeps the status and uses the server detail as the message', () => {
    const e = new ApiError(409, 'Transcript changed')
    expect(e.status).toBe(409)
    expect(e.message).toBe('Transcript changed')
  })

  it('carries the code the server sends with the detail', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ detail: 'malformed', code: 'malformed_reply' }),
      { status: 502, headers: { 'Content-Type': 'application/json' } },
    )))
    try {
      await expect(api.generateAnalysis('t1', { template: 'summary' })).rejects.toMatchObject({
        name: 'ApiError', status: 502, message: 'malformed', code: 'malformed_reply',
      })
    } finally {
      vi.unstubAllGlobals()
    }
  })

  it('is still an Error, so existing catch blocks keep working', () => {
    const e = new ApiError(500, 'boom')
    expect(e).toBeInstanceOf(Error)
    expect(e.name).toBe('ApiError')
  })
})
