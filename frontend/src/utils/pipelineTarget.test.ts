import { describe, expect, it } from 'vitest'
import { pipelineTargetToRun } from './pipelineTarget'

const targets = () => new Map([['t1', 'b1']])

describe('pipelineTargetToRun', () => {
  it('returns the target for the submitted, completed transcription with a result', () => {
    expect(pipelineTargetToRun(targets(), 't1', 'completed', true)).toEqual({ transcriptionId: 't1', bundleId: 'b1' })
  })
  it('returns null for another transcription', () => {
    expect(pipelineTargetToRun(targets(), 't2', 'completed', true)).toBeNull()
  })
  it('returns null while not completed', () => {
    expect(pipelineTargetToRun(targets(), 't1', 'processing', true)).toBeNull()
    expect(pipelineTargetToRun(targets(), 't1', null, true)).toBeNull()
  })
  it('returns null without a result or transcription id', () => {
    expect(pipelineTargetToRun(targets(), 't1', 'completed', false)).toBeNull()
    expect(pipelineTargetToRun(targets(), null, 'completed', true)).toBeNull()
  })
  it('returns null without any target', () => {
    expect(pipelineTargetToRun(new Map(), 't1', 'completed', true)).toBeNull()
  })
  it('keeps both submissions runnable', () => {
    const m = new Map([['a', 'b1'], ['b', 'b2']])
    expect(pipelineTargetToRun(m, 'b', 'completed', true)).toEqual({ transcriptionId: 'b', bundleId: 'b2' })
    expect(pipelineTargetToRun(m, 'a', 'completed', true)).toEqual({ transcriptionId: 'a', bundleId: 'b1' })
  })
  it('returns null once the caller has consumed the entry', () => {
    const m = new Map([['a', 'b1']])
    const first = pipelineTargetToRun(m, 'a', 'completed', true)
    expect(first).not.toBeNull()
    m.delete('a')
    expect(pipelineTargetToRun(m, 'a', 'completed', true)).toBeNull()
  })
})
