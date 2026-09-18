import { describe, it, expect } from 'vitest'
import { formatUtteranceRange, isInAnyRange } from './utteranceRanges'

describe('formatUtteranceRange', () => {
  it('shows a full chunk 1-based and inclusive', () => {
    expect(formatUtteranceRange([450, 500])).toBe('451–500')
  })

  it('shows the first chunk starting at 1', () => {
    expect(formatUtteranceRange([0, 50])).toBe('1–50')
  })

  it('shows a short last chunk', () => {
    expect(formatUtteranceRange([800, 841])).toBe('801–841')
  })

  it('collapses a single-utterance range to one number', () => {
    expect(formatUtteranceRange([7, 8])).toBe('8')
  })
})

describe('isInAnyRange', () => {
  const ranges: [number, number][] = [[450, 500], [600, 650]]

  it('includes the first index of a range', () => {
    expect(isInAnyRange(450, ranges)).toBe(true)
  })

  it('excludes the end index because ranges are half-open', () => {
    expect(isInAnyRange(500, ranges)).toBe(false)
  })

  it('finds an index inside a later range', () => {
    expect(isInAnyRange(649, ranges)).toBe(true)
  })

  it('is false when there are no ranges', () => {
    expect(isInAnyRange(0, [])).toBe(false)
  })
})
