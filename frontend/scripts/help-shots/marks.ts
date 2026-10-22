import type { ShotMeta } from '../../src/help/shotMeta.ts'

export interface Box {
  x: number
  y: number
  w: number
  h: number
}

const TOLERANCE = 2

const round = (v: number): number => Math.round(v * 10) / 10

/**
 * Turn page-relative element boxes into marks relative to the clip.
 * `selectors` is only used for error messages.
 */
export function computeMarks(clip: Box, marks: (Box | null)[], selectors: string[]): ShotMeta {
  return {
    width: round(clip.w),
    height: round(clip.h),
    marks: marks.map((box, i) => {
      const n = i + 1
      const selector = selectors[i]
      if (box === null) throw new Error(`mark ${n} (${selector}) not found`)
      const outside =
        box.x < clip.x - TOLERANCE ||
        box.y < clip.y - TOLERANCE ||
        box.x + box.w > clip.x + clip.w + TOLERANCE ||
        box.y + box.h > clip.y + clip.h + TOLERANCE
      if (outside) throw new Error(`mark ${n} (${selector}) outside clip`)
      return {
        n,
        x: round(box.x - clip.x),
        y: round(box.y - clip.y),
        w: round(box.w),
        h: round(box.h),
      }
    }),
  }
}
