/** Recorded marker boxes of a help screenshot, in CSS px relative to the clip. */
export interface ShotMeta {
  width: number
  height: number
  marks: { n: number; x: number; y: number; w: number; h: number }[]
}
