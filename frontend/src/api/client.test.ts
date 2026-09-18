import { describe, it, expect } from 'vitest'
import { ApiError } from './client'

describe('ApiError', () => {
  it('keeps the status and uses the server detail as the message', () => {
    const e = new ApiError(409, 'Transcript changed')
    expect(e.status).toBe(409)
    expect(e.message).toBe('Transcript changed')
  })

  it('is still an Error, so existing catch blocks keep working', () => {
    const e = new ApiError(500, 'boom')
    expect(e).toBeInstanceOf(Error)
    expect(e.name).toBe('ApiError')
  })
})
