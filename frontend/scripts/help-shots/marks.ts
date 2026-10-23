import type { ShotMeta } from '../../src/help/shotMeta.ts'

export interface Box {
  x: number
  y: number
  w: number
  h: number
}

/** Space around a clip: one value for all sides, or [top, right, bottom, left] like CSS. */
export type Pad = number | [number, number, number, number]

const TOLERANCE = 2

const round = (v: number): number => Math.round(v * 10) / 10

/** The smallest box that contains all the boxes. */
export function unionBox(boxes: Box[]): Box {
  const left = Math.min(...boxes.map((b) => b.x))
  const top = Math.min(...boxes.map((b) => b.y))
  const right = Math.max(...boxes.map((b) => b.x + b.w))
  const bottom = Math.max(...boxes.map((b) => b.y + b.h))
  return { x: left, y: top, w: right - left, h: bottom - top }
}

/**
 * Turn page-relative element boxes into marks relative to the clip. Each box is
 * widened by `margin` px on every side, so the frame and its numbered badge (drawn
 * over the frame's top-left corner) sit around the control instead of on it.
 * `selectors` is only used for error messages.
 */
export function computeMarks(clip: Box, marks: (Box | null)[], selectors: string[], margin = 0): ShotMeta {
  return {
    width: round(clip.w),
    height: round(clip.h),
    marks: marks.map((found, i) => {
      const n = i + 1
      const selector = selectors[i]
      if (found === null) throw new Error(`mark ${n} (${selector}) not found`)
      const box = { x: found.x - margin, y: found.y - margin, w: found.w + 2 * margin, h: found.h + 2 * margin }
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

/**
 * The screenshot clip: the union of the element boxes, snapped outward to whole
 * pixels and padded, clamped to the viewport. Throws when the boxes themselves
 * reach outside the viewport, because the image would then show less than the
 * recorded clip size.
 */
export function clipFor(boxes: Box[], pad: Pad, viewport: { width: number; height: number }): Box {
  const [padTop, padRight, padBottom, padLeft] = typeof pad === 'number' ? [pad, pad, pad, pad] : pad
  const united = unionBox(boxes)
  const left = Math.floor(united.x)
  const top = Math.floor(united.y)
  const right = Math.ceil(united.x + united.w)
  const bottom = Math.ceil(united.y + united.h)
  if (left < -TOLERANCE || top < -TOLERANCE || right > viewport.width + TOLERANCE || bottom > viewport.height + TOLERANCE) {
    throw new Error(`clip ${left},${top}–${right},${bottom} does not fit in the ${viewport.width}×${viewport.height} viewport`)
  }
  const x = Math.max(0, left - padLeft)
  const y = Math.max(0, top - padTop)
  return {
    x,
    y,
    w: Math.min(viewport.width, right + padRight) - x,
    h: Math.min(viewport.height, bottom + padBottom) - y,
  }
}
