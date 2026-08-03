export function singleConfiguredModel(models: string[]): string | null {
  return models.length === 1 ? models[0] : null
}

export function resolveModel(models: string[], fallback: string): string {
  return singleConfiguredModel(models) ?? fallback
}
