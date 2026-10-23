import { describe, it, expect } from 'vitest'
import { clipFor, computeMarks, unionBox } from './marks.ts'

const clip = { x: 100, y: 50, w: 1000, h: 300 }

describe('computeMarks', () => {
  it('makes boxes relative to the clip', () => {
    expect(computeMarks(clip, [{ x: 110, y: 60, w: 200, h: 40 }], ['a']).marks[0]).toEqual({
      n: 1, x: 10, y: 10, w: 200, h: 40,
    })
  })

  it('numbers marks in order and rounds to 0.1', () => {
    const meta = computeMarks(
      clip,
      [{ x: 110, y: 60, w: 20, h: 4 }, { x: 110.04, y: 60.06, w: 20.26, h: 4.449 }],
      ['a', 'b'],
    )
    expect(meta.marks[1]).toEqual({ n: 2, x: 10, y: 10.1, w: 20.3, h: 4.4 })
  })

  it('throws for a missing element', () => {
    expect(() => computeMarks(clip, [null], ['[data-help="x"]'])).toThrow('mark 1 ([data-help="x"]) not found')
  })

  it('throws for a box outside the clip', () => {
    expect(() => computeMarks(clip, [{ x: 1200, y: 60, w: 50, h: 10 }], ['b'])).toThrow('mark 1 (b) outside clip')
  })

  it('tolerates up to 2 px outside', () => {
    expect(() => computeMarks(clip, [{ x: 98.5, y: 60, w: 50, h: 10 }], ['b'])).not.toThrow()
  })

  it('widens each box by the margin', () => {
    expect(computeMarks(clip, [{ x: 120, y: 70, w: 50, h: 10 }], ['a'], 8).marks[0]).toEqual({
      n: 1, x: 12, y: 12, w: 66, h: 26,
    })
  })

  it('checks the widened box against the clip', () => {
    expect(() => computeMarks(clip, [{ x: 104, y: 70, w: 50, h: 10 }], ['a'], 8)).toThrow('mark 1 (a) outside clip')
  })

  it('reports the clip size', () => {
    expect(computeMarks(clip, [], []).width).toBe(1000)
    expect(computeMarks(clip, [], []).height).toBe(300)
  })
})

describe('clipFor', () => {
  const viewport = { width: 1280, height: 800 }

  it('snaps one box outward to whole pixels', () => {
    expect(clipFor([{ x: 10.4, y: 20.6, w: 100.2, h: 50.1 }], 0, viewport)).toEqual({
      x: 10, y: 20, w: 101, h: 51,
    })
  })

  it('unites several boxes', () => {
    expect(
      clipFor([{ x: 10, y: 20, w: 100, h: 50 }, { x: 50, y: 100, w: 200, h: 30 }], 0, viewport),
    ).toEqual({ x: 10, y: 20, w: 240, h: 110 })
  })

  it('pads the box and stops at the viewport edges', () => {
    expect(clipFor([{ x: 4, y: 100, w: 1270, h: 50 }], 8, viewport)).toEqual({
      x: 0, y: 92, w: 1280, h: 66,
    })
  })

  it('pads each side separately', () => {
    expect(clipFor([{ x: 100, y: 100, w: 100, h: 100 }], [4, 10, 0, 20], viewport)).toEqual({
      x: 80, y: 96, w: 130, h: 104,
    })
  })

  it('throws when the boxes do not fit in the viewport', () => {
    expect(() => clipFor([{ x: 0, y: 500, w: 100, h: 400 }], 0, viewport)).toThrow('does not fit')
  })
})

describe('unionBox', () => {
  it('returns the box around all boxes', () => {
    expect(unionBox([{ x: 10, y: 20, w: 5, h: 5 }, { x: 0, y: 30, w: 4, h: 10 }])).toEqual({ x: 0, y: 20, w: 15, h: 20 })
  })
})
