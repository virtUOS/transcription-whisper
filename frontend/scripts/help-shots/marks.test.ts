import { describe, it, expect } from 'vitest'
import { computeMarks } from './marks.ts'

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

  it('reports the clip size', () => {
    expect(computeMarks(clip, [], []).width).toBe(1000)
    expect(computeMarks(clip, [], []).height).toBe(300)
  })
})
