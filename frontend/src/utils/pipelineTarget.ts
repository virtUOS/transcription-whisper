export interface PipelineTarget {
  transcriptionId: string
  bundleId: string
}

/**
 * Bundle steps run only for a transcription that was submitted with a bundle.
 * `targets` maps transcription id to bundle id, so several submissions can be pending at once.
 * The caller deletes the entry before running, so the steps cannot run twice.
 */
export function pipelineTargetToRun(
  targets: ReadonlyMap<string, string>,
  transcriptionId: string | null,
  status: string | null,
  hasResult: boolean,
): PipelineTarget | null {
  if (!transcriptionId || status !== 'completed' || !hasResult) return null
  const bundleId = targets.get(transcriptionId)
  return bundleId ? { transcriptionId, bundleId } : null
}
