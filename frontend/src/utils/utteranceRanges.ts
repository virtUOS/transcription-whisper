/** A half-open, 0-based utterance index range, exactly as the backend stores it. */
export type UtteranceRange = [number, number]

/** "451–500" for [450, 500): 1-based and inclusive, matching the row numbers the table shows. */
export function formatUtteranceRange([start, end]: UtteranceRange): string {
  const first = start + 1
  const last = end
  return first === last ? `${first}` : `${first}–${last}`
}

export function isInAnyRange(index: number, ranges: UtteranceRange[]): boolean {
  return ranges.some(([start, end]) => index >= start && index < end)
}
