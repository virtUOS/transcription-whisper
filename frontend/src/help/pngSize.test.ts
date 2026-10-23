import { describe, expect, it } from 'vitest'
import { pngSize } from './pngSize'

function header(width: number, height: number): Uint8Array {
  const buf = new Uint8Array(33)
  buf.set([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
  buf.set([0, 0, 0, 13, 0x49, 0x48, 0x44, 0x52], 8)
  const view = new DataView(buf.buffer)
  view.setUint32(16, width)
  view.setUint32(20, height)
  return buf
}

describe('pngSize', () => {
  it('reads big-endian width and height from IHDR', () => {
    expect(pngSize(header(1280, 800))).toEqual({ width: 1280, height: 800 })
    expect(pngSize(header(70000, 258))).toEqual({ width: 70000, height: 258 })
  })

  it('rejects data that is not a PNG', () => {
    expect(() => pngSize(new Uint8Array(40))).toThrow()
  })
})
